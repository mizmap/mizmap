"""Runtime configuration. Resolves settings from env vars > config.toml > defaults.

When frozen as a Windows exe:
  - `tile_cache_dir` defaults to `%LOCALAPPDATA%\\MizMap\\tiles`
  - `config.toml` is read from `%APPDATA%\\MizMap\\config.toml` (see [paths.py](paths.py))
  - `ensure_config_file()` writes a commented template on first run

In dev mode the config file is only consulted when `MIZMAP_CONFIG_FILE` points
at one, so a stray `config.toml` in the repo won't accidentally bend behavior.
"""

from __future__ import annotations

import logging
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from mizmap.paths import default_tile_cache_dir, is_frozen, user_config_dir

log = logging.getLogger(__name__)

_CONFIG_FILENAME = "config.toml"

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

# --- Map tiles (advanced) ----------------------------------------------------
# Upstream tile URL. The local proxy fetches + caches on first request.
# tile_url = "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"

# Attribution shown on the map.
# tile_attribution = "Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap (CC-BY-SA)"

# Where tiles are cached on disk. Defaults to %LOCALAPPDATA%\\MizMap\\tiles.
# tile_cache_dir = "C:/path/to/tiles"
"""


def _config_file_path() -> Path | None:
    """Resolve which `config.toml` to read, or None if no file should be consulted.

    Frozen: `%APPDATA%\\MizMap\\config.toml`. Dev: only when `MIZMAP_CONFIG_FILE` is set.
    """
    explicit = os.environ.get("MIZMAP_CONFIG_FILE")
    if explicit:
        return Path(explicit)
    if is_frozen():
        return user_config_dir() / _CONFIG_FILENAME
    return None


def _load_config_file() -> dict[str, object]:
    path = _config_file_path()
    if path is None or not path.is_file():
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

    @classmethod
    def from_env(cls) -> "Settings":
        file_cfg = _load_config_file()
        tile_cache_raw = _resolve(file_cfg, "MIZMAP_TILE_CACHE_DIR", "tile_cache_dir", None)
        tile_cache_dir = (
            Path(str(tile_cache_raw)) if tile_cache_raw is not None else default_tile_cache_dir()
        )
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
        )
