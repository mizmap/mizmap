"""Resource & writable-path resolution for MizMap.

Three runtime modes to distinguish:

1. **Source tree** — running `uv run mizmap serve` from a checkout. Resources
   live at their on-disk paths under the repo root.
2. **Installed wheel** — `pip install mizmap`. Package data is alongside the
   installed `mizmap/` package; `web/` is force-included as `mizmap/_web/`
   (see [pyproject.toml](../pyproject.toml)).
3. **PyInstaller-frozen exe** — `sys.frozen` is set, `sys._MEIPASS` points
   at the bundle root (one-folder mode: alongside `mizmap.exe` under
   `_internal/`).

For *read-only* resources (web dir, bundled data files) we resolve at runtime
and prefer the first candidate that exists. For *writable* user state (tile
cache, config file) we route to per-user Windows directories when frozen,
and to the current working directory otherwise — so dev iteration keeps the
cache visible in the repo, while installed users get the conventional
`%LOCALAPPDATA%` / `%APPDATA%` locations without polluting random folders.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """True when running inside a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def _bundle_root() -> Path:
    """PyInstaller bundle root. Only meaningful when frozen."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(sys.executable).parent


def web_dir() -> Path:
    """Directory containing the static viewer assets (index.html, main.js, ...).

    Returns the first existing candidate. If none exist, returns the source-tree
    path so the caller can log a useful "directory not found at X" warning.
    """
    here = Path(__file__).resolve().parent  # mizmap/
    candidates: list[Path] = []
    if is_frozen():
        candidates.append(_bundle_root() / "web")
    candidates.extend(
        [
            here / "_web",          # wheel install (force-included)
            here.parent / "web",    # source tree
        ]
    )
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[-1]


def user_cache_dir() -> Path:
    """Root for writable, regenerable caches (tiles, etc.).

    Frozen on Windows: `%LOCALAPPDATA%\\MizMap`. Otherwise: current working
    directory (so `./cache/tiles` keeps working in dev).
    """
    if is_frozen() and sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            return Path(local) / "MizMap"
    return Path.cwd()


def user_config_dir() -> Path:
    """Root for writable user configuration (config.toml).

    Frozen on Windows: `%APPDATA%\\MizMap`. Otherwise: current working directory.
    """
    if is_frozen() and sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "MizMap"
    return Path.cwd()


def default_tile_cache_dir() -> Path:
    """Default `tile_cache_dir` setting.

    Frozen: `<user_cache_dir>/tiles`. Dev: `./cache/tiles` (unchanged).
    """
    if is_frozen():
        return user_cache_dir() / "tiles"
    return Path("cache") / "tiles"
