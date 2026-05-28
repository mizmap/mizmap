"""Runtime configuration. Resolves settings from env vars > config.toml > defaults.

The `config.toml` lives in `user_config_dir()` — `%APPDATA%\\MizMap` when frozen,
the current working directory in dev (gitignored). It's read in **both** modes so
the in-app Settings panel (`/api/settings`) works the same everywhere; env vars
still win over file values, and a setting pinned by an env var shows as locked in
the UI. `MIZMAP_CONFIG_FILE` overrides the path (used by tests).

When frozen as a Windows exe:
  - `tile_cache_dir` defaults to `%LOCALAPPDATA%\\MizMap\\tiles`
  - `ensure_config_file()` writes a commented template on first run
"""

from __future__ import annotations

import logging
import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

from mizmap.paths import default_tile_cache_dir, is_frozen, user_config_dir

log = logging.getLogger(__name__)

_CONFIG_FILENAME = "config.toml"

# Editable-setting key → environment variable. Env values win over the file, so
# the Settings UI shows these as locked when the corresponding var is set.
_ENV_NAMES = {
    "http_host": "MIZMAP_HTTP_HOST",
    "http_port": "MIZMAP_HTTP_PORT",
    "grpc_host": "MIZMAP_GRPC_HOST",
    "grpc_port": "MIZMAP_GRPC_PORT",
    "dcs_install_dir": "MIZMAP_DCS_INSTALL_DIR",
    "tile_url": "MIZMAP_TILE_URL",
    "tile_attribution": "MIZMAP_TILE_ATTRIBUTION",
    "tile_cache_dir": "MIZMAP_TILE_CACHE_DIR",
}

_TEMPLATE = """\
# MizMap configuration. Uncomment a line to override the default. Restart MizMap
# after editing. Environment variables (MIZMAP_HTTP_PORT, etc.) still win over
# values here.

# --- Network -----------------------------------------------------------------
# Bind address. "0.0.0.0" listens on all interfaces (needed for LAN tablets).
# "127.0.0.1" restricts to the local machine.
# http_host = "0.0.0.0"

# Port for the web viewer + WebSocket.
# http_port = 8766

# --- DCS-gRPC connection -----------------------------------------------------
# Host running DCS-gRPC. Use 127.0.0.1 when MizMap and DCS run on the same PC.
# grpc_host = "127.0.0.1"

# DCS-gRPC port (rust-server default is 50051).
# grpc_port = 50051

# --- DCS install -------------------------------------------------------------
# DCS World install directory (used to read terrain navaid data for the Navaids
# layer). Auto-detected from the registry / common paths when left unset.
# dcs_install_dir = "C:/DCS"

# --- Map tiles (advanced) ----------------------------------------------------
# Upstream tile URL. The local proxy fetches + caches on first request.
# tile_url = "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"

# Attribution shown on the map.
# tile_attribution = "Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap (CC-BY-SA)"

# Where tiles are cached on disk. Defaults to %LOCALAPPDATA%\\MizMap\\tiles.
# tile_cache_dir = "C:/path/to/tiles"
"""


def _config_file_path() -> Path:
    """Resolve the `config.toml` path (read + written).

    `MIZMAP_CONFIG_FILE` overrides; otherwise `user_config_dir()/config.toml`
    (`%APPDATA%\\MizMap` frozen, cwd in dev).
    """
    explicit = os.environ.get("MIZMAP_CONFIG_FILE")
    if explicit:
        return Path(explicit)
    return user_config_dir() / _CONFIG_FILENAME


def detect_dcs_install_dir() -> Path | None:
    """Best-effort auto-detect of the DCS World install directory (Windows).

    Tries the registry path Eagle Dynamics writes on install (authoritative,
    works for non-default install locations), then a few common locations.
    Returns the first directory that exists and looks like a DCS install
    (`Mods/terrains` present), or None.
    """
    candidates: list[Path] = []
    if sys.platform == "win32":
        try:
            import winreg

            for sub in (r"Software\Eagle Dynamics\DCS World",
                        r"Software\Eagle Dynamics\DCS World OpenBeta"):
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub) as key:
                        val, _ = winreg.QueryValueEx(key, "Path")
                        if val:
                            candidates.append(Path(val))
                except OSError:
                    continue
        except ImportError:
            pass
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        candidates += [
            Path(pf) / "Eagle Dynamics" / "DCS World",
            Path(pf) / "Eagle Dynamics" / "DCS World OpenBeta",
            Path(r"C:\DCS"),
        ]
    for c in candidates:
        try:
            if c.is_dir() and (c / "Mods" / "terrains").is_dir():
                return c
        except OSError:
            continue
    return None


def _load_config_file() -> dict[str, object]:
    path = _config_file_path()
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        log.warning("config.toml at %s could not be loaded: %s — using defaults", path, exc)
        return {}
    if not isinstance(data, dict):
        log.warning("config.toml at %s: top-level is not a table — ignored", path)
        return {}
    log.info("config: loaded %d setting(s) from %s", len(data), path)
    return data


def ensure_config_file() -> Path | None:
    """If frozen and `%APPDATA%/MizMap/config.toml` is missing, write a commented template.

    Returns the path that was written, or None if nothing was done. Safe to call
    on every startup — only the first run does work.
    """
    if not is_frozen():
        return None
    cfg_dir = user_config_dir()
    cfg_path = cfg_dir / _CONFIG_FILENAME
    if cfg_path.exists():
        return None
    try:
        cfg_dir.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(_TEMPLATE, encoding="utf-8")
    except OSError as exc:
        log.warning("could not write config template to %s: %s", cfg_path, exc)
        return None
    log.info("config: wrote template to %s", cfg_path)
    return cfg_path


def _resolve(file_cfg: dict[str, object], env_name: str, key: str, default: object) -> object:
    """env > file > default. Env values are strings; file values keep TOML types."""
    env_val = os.environ.get(env_name)
    if env_val is not None:
        return env_val
    if key in file_cfg:
        return file_cfg[key]
    return default


@dataclass(frozen=True)
class Settings:
    http_host: str
    http_port: int
    grpc_host: str
    grpc_port: int
    tile_url: str
    tile_attribution: str
    tile_cache_dir: Path
    # DCS World install dir (for terrain Beacons.lua, navaids). None = not
    # configured and auto-detect failed.
    dcs_install_dir: Path | None

    @classmethod
    def from_env(cls) -> "Settings":
        file_cfg = _load_config_file()
        tile_cache_raw = _resolve(file_cfg, "MIZMAP_TILE_CACHE_DIR", "tile_cache_dir", None)
        tile_cache_dir = (
            Path(str(tile_cache_raw)) if tile_cache_raw is not None else default_tile_cache_dir()
        )
        # env > file > auto-detect for the DCS install dir.
        dcs_raw = _resolve(file_cfg, "MIZMAP_DCS_INSTALL_DIR", "dcs_install_dir", None)
        dcs_dir = Path(str(dcs_raw)) if dcs_raw else detect_dcs_install_dir()
        return cls(
            http_host=str(_resolve(file_cfg, "MIZMAP_HTTP_HOST", "http_host", "0.0.0.0")),
            http_port=int(_resolve(file_cfg, "MIZMAP_HTTP_PORT", "http_port", 8766)),
            grpc_host=str(_resolve(file_cfg, "MIZMAP_GRPC_HOST", "grpc_host", "127.0.0.1")),
            grpc_port=int(_resolve(file_cfg, "MIZMAP_GRPC_PORT", "grpc_port", 50051)),
            tile_url=str(
                _resolve(
                    file_cfg,
                    "MIZMAP_TILE_URL",
                    "tile_url",
                    "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
                )
            ),
            tile_attribution=str(
                _resolve(
                    file_cfg,
                    "MIZMAP_TILE_ATTRIBUTION",
                    "tile_attribution",
                    "Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap (CC-BY-SA)",
                )
            ),
            tile_cache_dir=tile_cache_dir.resolve(),
            dcs_install_dir=dcs_dir,
        )


def env_locked_keys() -> set[str]:
    """Editable keys currently pinned by an environment variable (file can't override)."""
    return {k for k, env in _ENV_NAMES.items() if os.environ.get(env) is not None}


def configured_value(key: str) -> object | None:
    """The explicitly-set env-or-file value for a key, or None.

    Unlike the resolved `Settings`, this excludes defaults and auto-detection —
    so the Settings UI can show a blank field when a value is only auto-detected
    (vs. pinned), and offer the detected value as a placeholder instead.
    """
    env_name = _ENV_NAMES.get(key)
    if env_name and os.environ.get(env_name) is not None:
        return os.environ[env_name]
    return _load_config_file().get(key)


def _toml_value(v: object) -> str:
    """Serialize a scalar to a TOML literal (str/int/float/bool only)."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    # Basic string: escape backslash + double-quote so Windows paths survive.
    s = str(v).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def update_config_file(updates: dict[str, object]) -> Path:
    """Merge `updates` into config.toml and write it back, returning the path.

    A value of None removes the key (revert to default/auto). Existing keys not
    in `updates` (e.g. advanced tile_* settings) are preserved. The file is
    regenerated, so prior inline comments are not kept.
    """
    path = _config_file_path()
    current = dict(_load_config_file())
    for key, val in updates.items():
        if val is None:
            current.pop(key, None)
        else:
            current[key] = val
    lines = [
        "# MizMap configuration — managed by the in-app Settings panel.",
        "# Environment variables (MIZMAP_*) still override these. Restart MizMap",
        "# to apply network changes (port/host).",
        "",
    ]
    for key in sorted(current):
        lines.append(f"{key} = {_toml_value(current[key])}")
    body = "\n".join(lines) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    log.info("config: wrote %d setting(s) to %s", len(current), path)
    return path
