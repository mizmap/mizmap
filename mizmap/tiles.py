"""Local tile proxy + on-disk cache.

The frontend points at `/tiles/{source}/{z}/{x}/{y}` (served by `mizmap.server`)
instead of the public upstream URLs. On request we look in the on-disk cache;
on miss we fetch from the source's upstream URL, save to disk, and serve. Tiles
are immutable — there's no TTL or revalidation — so a long-lived cache is a
strict win for dev iteration, LAN consistency (multiple viewers share one warmed
cache), latency, and upstream rate-limit politeness.

Multi-source: every selectable basemap (see `mizmap/basemaps.py`) is proxied the
same way, each under its own `cache_dir/<source>/` subtree, so switching
basemaps still never bypasses the cache. The source id is validated against the
registry before any filesystem/network use.

Concurrent misses for the same tile race to fetch independently. Acceptable:
collisions are rare in practice and serialising would add complexity.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import httpx

from mizmap import __version__
from mizmap.basemaps import Basemap

log = logging.getLogger(__name__)

# Polite identifier so OpenTopoMap (and similar community-run tile servers)
# can see who's hitting them. No public URL claimed since MizMap doesn't have
# one yet; just identify the project.
_USER_AGENT = f"MizMap/{__version__} (MizMap for DCS World)"

# Periodic summary cadence — log a one-liner every Nth request.
_LOG_EVERY = 100


class TileCache:
    """Resolves tile URLs against a local on-disk cache, across basemap sources.

    One instance per `mizmap serve` process. Holds the basemap registry (keyed
    by id), the cache directory, an httpx client, and the hit/miss counters.
    """

    def __init__(self, basemaps: list[Basemap], cache_dir: Path) -> None:
        self._sources = {b.id: b for b in basemaps}
        self._cache_dir = cache_dir
        # `astral.sh/uv` ships httpx via FastAPI's transitive deps; reuse a
        # single client for connection pooling.
        self._client = httpx.AsyncClient(
            headers={"User-Agent": _USER_AGENT},
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=True,
        )
        # Try to create the cache dir up front; log + continue if it fails so
        # the proxy still works (it'll just refetch every tile).
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            self._writable = True
        except OSError as exc:
            log.warning("tile cache dir %s not writable (%s) — running without cache", cache_dir, exc)
            self._writable = False
        self._hits = 0
        self._misses = 0
        self._errors = 0

    async def aclose(self) -> None:
        await self._client.aclose()

    def has_source(self, source: str) -> bool:
        return source in self._sources

    def content_type(self, source: str) -> str:
        return self._sources[source].content_type

    def _tile_path(self, source: str, z: int, x: int, y: int) -> Path:
        # Path traversal protection: source is validated against the registry by
        # has_source(); z/x/y are non-negative ints enforced by the URL converter.
        return self._cache_dir / source / str(z) / str(x) / f"{y}.{self._sources[source].ext}"

    def _upstream_url(self, source: str, z: int, x: int, y: int) -> str:
        bm = self._sources[source]
        # `{s}` subdomain (a/b/c on OSM/OpenTopoMap) doesn't matter for us — we're
        # the source for downstream clients. Pick the first deterministically.
        sub = bm.subdomains[0] if bm.subdomains else "a"
        return (
            bm.upstream_url
            .replace("{s}", sub)
            .replace("{z}", str(z))
            .replace("{x}", str(x))
            .replace("{y}", str(y))
        )

    def _maybe_log_stats(self) -> None:
        total = self._hits + self._misses + self._errors
        if total > 0 and total % _LOG_EVERY == 0:
            ratio = (self._hits / total) * 100 if total else 0.0
            log.info(
                "tiles: %d hits, %d misses, %d errors (%.1f%% hit rate)",
                self._hits,
                self._misses,
                self._errors,
                ratio,
            )

    async def fetch(self, source: str, z: int, x: int, y: int) -> tuple[bytes, str]:
        """Return (tile_bytes, cache_status) for the tile from `source`.

        `cache_status` is "hit" or "miss" for the response `X-Tile-Cache`
        header. Caller must validate `source` via `has_source()` first. On
        upstream failure, raises httpx.HTTPError (the server route translates
        to a 502).
        """
        path = self._tile_path(source, z, x, y)
        if self._writable and path.is_file():
            try:
                data = await asyncio.to_thread(path.read_bytes)
                self._hits += 1
                self._maybe_log_stats()
                return data, "hit"
            except OSError as exc:
                # Disk read failed — fall through to refetch.
                log.warning("tile cache read failed for %s (%s) — refetching", path, exc)

        url = self._upstream_url(source, z, x, y)
        try:
            resp = await self._client.get(url)
            resp.raise_for_status()
        except httpx.HTTPError:
            self._errors += 1
            self._maybe_log_stats()
            raise
        data = resp.content
        self._misses += 1
        self._maybe_log_stats()

        # Persist best-effort. Failure to write doesn't fail the response.
        if self._writable:
            try:
                await asyncio.to_thread(_atomic_write, path, data)
            except OSError as exc:
                log.warning("tile cache write failed for %s (%s)", path, exc)

        return data, "miss"


def _atomic_write(path: Path, data: bytes) -> None:
    """Write `data` to `path` via a temp file in the same dir.

    Avoids leaving a half-written file if the process is killed mid-write
    or if two writers race. The temp suffix includes the pid so concurrent
    writers don't clobber each other's temp names.
    """
    import os

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def clear_cache(cache_dir: Path) -> tuple[int, int]:
    """Wipe every cached tile under `cache_dir`. Returns (files_deleted, bytes_freed)."""
    if not cache_dir.is_dir():
        return (0, 0)
    files = 0
    total_bytes = 0
    for p in cache_dir.rglob("*"):
        if p.is_file():
            try:
                total_bytes += p.stat().st_size
                p.unlink()
                files += 1
            except OSError as exc:
                log.warning("failed to delete %s: %s", p, exc)
    # Remove now-empty subdirectories (bottom-up).
    for p in sorted(cache_dir.rglob("*"), key=lambda q: -len(q.parts)):
        if p.is_dir():
            try:
                p.rmdir()
            except OSError:
                pass  # Not empty — leave it.
    return (files, total_bytes)
