import json
import logging
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Any, NamedTuple, Union

logger = logging.getLogger(__name__)


class CacheRec(NamedTuple):
    name: str
    url: str
    ext: str
    content_type: str
    filename: str


class Cache:
    # index filename
    indexfilename = "index.json"

    rootdir: Path
    # dict[name] = CacheRec
    _pages: dict[str, CacheRec]

    def __init__(self, rootdir: Path):
        logger.debug("cache: [%s] created", rootdir)
        self._set_cache_dir(rootdir)

    def _set_cache_dir(self, dir: Path) -> None:
        cache_dir = dir.resolve()
        if cache_dir.is_file():
            raise ValueError(f"{cache_dir} is not a directory but a file")

        self.rootdir = cache_dir
        os.makedirs(self.rootdir, exist_ok=True)

        indexfilename = self.rootdir / self.indexfilename
        self._load_indexfile(indexfilename)

    def _load_indexfile(self, indexfilename: Path) -> None:
        if indexfilename.is_file():
            logger.debug("cache: loading index from [%s]", indexfilename)
            with indexfilename.open() as f:
                # list[url, (datetimestr, filename)]
                index: list[CacheRec] = json.load(f)

            self._pages = {}
            rec: CacheRec
            for rec in index:
                tp = CacheRec(*rec)
                self._pages[tp.name] = tp
        else:
            logger.debug("cache: empty index [%s]", indexfilename)
            self._pages = {}

    def save(self) -> None:
        logger.debug("cache: saving")
        index: list[Any] = list(self._pages.values())

        indexfilename = self.rootdir / self.indexfilename
        tmp = indexfilename.with_suffix(".tmp")
        with tmp.open("w") as f:
            json.dump(index, f)

        tmp.rename(indexfilename)

    def destroy_cache(self) -> None:
        logger.debug("cache: destroy_cache")
        if self.rootdir.exists():
            shutil.rmtree(self.rootdir)
        self._pages = {}

    def get_path(self, name: str) -> tuple[str, Path]:
        rec = self._pages[name]
        filename = self.rootdir / rec.filename
        return rec.content_type, filename

    def list(self) -> list[str]:
        return list(self._pages.keys())

    def get(self, name: str) -> Union[str, bytes]:
        content_type, filename = self.get_path(name)
        if content_type.startswith("text/"):
            return filename.read_text("utf-8")
        else:
            return filename.read_bytes()

    def set(
        self, name: str, url: str, ext: str, content_type: str, body: bytes
    ) -> None:
        logger.debug("cache: setting [%s]", url)
        strfilename = uuid.uuid4().hex

        ext = re.sub(r"[^0-9a-zA-Z]", "", ext)[:4]
        if ext:
            strfilename += "." + ext

        filename = self.rootdir / strfilename
        filename.write_bytes(body)

        tp = self._pages.get(url)
        if tp:
            oldpath = self.rootdir / tp.filename
            try:
                oldpath.unlink()
            except Exception:
                # ignore error
                logger.exception("cache: Failed to delete old cache [%s]", url)

        self._pages[name] = CacheRec(name, url, ext, content_type, strfilename)
