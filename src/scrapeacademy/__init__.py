__version__ = "0.0.1"

import asyncio
import logging
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Awaitable, Union, cast

from .context import Context

logger = logging.getLogger(__name__)


class wrapper:
    def __getattr__(self, name: str) -> Any:
        return getattr(_context.get(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(_context.get(), name, value)


_context: ContextVar[Context] = ContextVar("var", default=Context())
context: Context = cast(Context, wrapper())


def init_context(
    cache_dir: Union[Path, str, None] = None,
) -> None:
    logger.debug("start context %s", cache_dir)
    _context.get().open_cache(cache_dir)


def run(
    func: Awaitable[Any],
) -> Any:
    async def _run() -> Any:
        try:
            ret = await func
        finally:
            await context.close()
        return ret

    ret = asyncio.run(_run())
    logger.debug("finished")
    return ret
