import asyncio
import logging
import mimetypes
import os
import re
from pathlib import Path
from typing import Any, Optional, Union
from urllib.parse import urlparse

import aiohttp
from aiolimiter import AsyncLimiter

from .cache import Cache
from .const import DEFAULT_CACHE_DIR_NAME

logger = logging.getLogger(__name__)


class Context:

    # Delay between requests to a site in seconds.
    request_delay: float = 0.1

    # concurrent requests
    concurrent_requests: int = 5

    allow_redirects: Optional[bool] = None

    max_redirects: Optional[int] = None

    headers: dict[str, Any]

    request_kwargs: dict[str, Any]

    # session
    _session: Optional[aiohttp.ClientSession] = None

    # cache
    _cache: Optional[Cache] = None

    @property
    def cache(self) -> Cache:
        if not self._cache:
            self._cache = self._create_cache()
        return self._cache

    def __init__(self) -> None:
        self.headers = {}
        self.request_kwargs = {}
        self._limiters: dict[str, AsyncLimiter] = {}
        self._actives: dict[str, asyncio.Semaphore] = {}

    def _create_cache(self, cache_dir: Union[Path, str, None] = None) -> Cache:
        logger.debug("initializing [%s]", cache_dir)
        if not cache_dir:
            cache_dir = Path.cwd() / DEFAULT_CACHE_DIR_NAME
        else:
            if isinstance(cache_dir, str):
                cache_dir = Path(cache_dir)
            cache_dir = cache_dir.expanduser().absolute()
        return Cache(cache_dir)

    def open_cache(self, cache_dir: Union[Path, str, None] = None) -> None:
        self._cache = self._create_cache(cache_dir)

    async def close(self) -> None:
        logger.debug("closing")
        if self._session:
            await self._session.close()
            self._session = None
        self.cache.save()

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = aiohttp.ClientSession()

        return self._session

    def _get_limiter(self, url: str) -> AsyncLimiter:
        host = urlparse(url).netloc
        limiter = self._limiters.get(host)
        if not limiter:
            limiter = self._limiters[host] = AsyncLimiter(1, self.request_delay)
        return limiter

    def _get_active_semaphore(self, url: str) -> asyncio.Semaphore:
        host = urlparse(url).netloc
        sem = self._actives.get(host)
        if not sem:
            sem = self._actives[host] = asyncio.Semaphore(self.concurrent_requests)
        return sem

    def _save(self, resp: aiohttp.ClientResponse, name: str, body: bytes) -> None:
        _, ext = os.path.splitext(resp.url.path)
        ext = re.sub(r"[^0-9a-zA-Z]", "", ext)[:4]
        if not ext:
            if resp.content_type:
                guess = mimetypes.guess_extension(resp.content_type)
                if guess:
                    ext = guess[1:]

        self.cache.set(name, str(resp.url), ext, resp.content_type, body)

    async def request(
        self,
        method: str,
        url: str,
        params: Optional[dict[str, Any]] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[str, bytes]:
        await self._get_limiter(url).acquire()
        sem = self._get_active_semaphore(url)

        async with sem:
            session = await self._get_session()
            headers = self.headers.copy()
            headers.update(kwargs.pop("headers", {}))

            allow_redirects = kwargs.pop("allow_redirects", self.allow_redirects)
            max_redirects = kwargs.pop("max_redirects", self.max_redirects)

            async with session.request(
                method,
                url,
                params=params,
                headers=headers,
                allow_redirects=allow_redirects,
                max_redirects=max_redirects,
                **kwargs,
            ) as resp:
                resp.raise_for_status()

                ret: Union[str, bytes]
                if resp.content_type.startswith("text/"):
                    ret = text = await resp.text()
                    body = text.encode("utf-8")

                else:
                    ret = body = await resp.read()

                if name:
                    self._save(resp, name, body)
        return ret

    async def get(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[str, bytes]:
        return await self.request("GET", url, params=params, name=name, **kwargs)

    async def post(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[str, bytes]:
        return await self.request("POST", url, params=params, name=name, **kwargs)

    def load(self, name: str) -> Union[bytes, str]:
        return self.cache.get(name)
