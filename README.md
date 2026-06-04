# MizMap

A live, moving-map viewer for **single-player** DCS World missions. Open a browser on your DCS PC — or on a tablet/phone on the same Wi-Fi — and watch your mission unfold on a real-world topographic map with full visibility into every unit you choose to see.

Inspired by [DCS MovingMap](https://movingmap.bergison.com), with one key difference: **you choose what's visible** — MizMap doesn't enforce the mission's in-game F10 view options.

> **Scope:** single-player only. Multiplayer is explicitly out of scope.
> **Status:** pre-1.0 (0.1.0). Usable from source or via the Windows installer; expect rough edges and breaking changes.

## Architecture

```
DCS World (Windows)
   │
   ├── DCS-gRPC rust-server (Hooks DLL)  ── gRPC :50051
   │
   ▼
MizMap backend (Python, FastAPI)
   ├── async gRPC client → unit/event streams
   ├── in-memory mission state
   ├── HTTP/WebSocket server (default :8766)
   └── serves the web viewer
   │
   ▼
MizMap viewer (browser, Leaflet + MIL-STD-2525 symbology)
   on the DCS PC and/or a LAN tablet
```

## Quickstart (development, on Mac/Linux, without DCS)

```bash
uv sync                          # install deps into .venv
./scripts/regen_protos.sh        # generate Python gRPC stubs

# Terminal 1 — start the mock DCS-gRPC server (canned scenario)
uv run python -m mizmap.dev.mock_server

# Terminal 2 — start the MizMap server
uv run mizmap serve

# Open the viewer
open http://localhost:8766
```

## Quickstart (real DCS on Windows — installer)

1. Install [DCS-gRPC rust-server](https://github.com/DCS-gRPC/rust-server) into DCS and enable `evalEnabled = true` in `Saved Games/DCS/Config/dcs-grpc.lua`.
2. Grab `mizmap-setup-<version>.exe` from the latest release and run it. The installer drops MizMap under `%LOCALAPPDATA%\Programs\MizMap\` (no admin needed) and adds a Start menu shortcut.
3. Launch **MizMap** from the Start menu. A tray icon appears and the viewer opens in your default browser automatically.
4. Right-click the tray icon to *Open viewer* in a new tab or *Quit MizMap*.

Per-user config lives at `%APPDATA%\MizMap\config.toml` (commented template written on first run — uncomment lines to override defaults). Tile cache at `%LOCALAPPDATA%\MizMap\tiles\` survives reinstalls.

> The installer is unsigned, so SmartScreen will show an "unknown publisher" warning the first time. Click *More info* → *Run anyway*.

## Quickstart (real DCS on Windows — from source)

1. Install [DCS-gRPC rust-server](https://github.com/DCS-gRPC/rust-server) into DCS.
2. Start DCS and load a single-player mission.
3. Run `mizmap serve` on the DCS PC (or another machine on the LAN — see `MIZMAP_GRPC_HOST`).
4. Open `http://<dcs-pc-ip>:8766` in any browser on the LAN.

## Configuration

Settings resolve from three places, highest priority first: environment variables (`MIZMAP_*`), a `config.toml` in the per-user config dir (`%APPDATA%\MizMap` when installed, the working dir in dev), then built-in defaults / auto-detection. Most keys are also editable live from the in-app **Settings** panel (the gear in the controls panel, or *Settings…* on the tray icon), which writes `config.toml` for you — no hand-editing required.

| Var | Default | Purpose |
|---|---|---|
| `MIZMAP_HTTP_HOST` | `0.0.0.0` | Bind address for the web/WS server (`0.0.0.0` = reachable by LAN tablets; `127.0.0.1` = local only). |
| `MIZMAP_HTTP_PORT` | `8766` | Port for the web/WS server. |
| `MIZMAP_GRPC_HOST` | `127.0.0.1` | Host running DCS-gRPC. |
| `MIZMAP_GRPC_PORT` | `50051` | DCS-gRPC port. |
| `MIZMAP_DCS_INSTALL_DIR` | auto-detect | DCS install folder, used to read the loaded theatre's navaids. Auto-detected from the registry + common paths on Windows. |
| `MIZMAP_TILE_URL` | OpenTopoMap | Upstream URL template for the **topographic** basemap (fetched on cache miss). |
| `MIZMAP_TILE_CACHE_DIR` | `./cache/tiles` | Where the local tile proxy stores its on-disk cache. |

The viewer offers three basemaps — **Topographic**, **Streets**, and **Satellite** — selectable from the controls panel (the choice rides the URL hash). Tiles are served by a local proxy at `/tiles/{source}/{z}/{x}/{y}` and cached per-source to disk on first fetch — so dev iteration doesn't burn the upstream rate limit, LAN viewers share one warm cache, and the map keeps working offline once warm. Wipe all sources with `mizmap clear-cache`.

## Development

See [`.journal/`](.journal/) for development notes per session (git-ignored —
local to the maintainer's machine). Longer-lived engineering notes that travel
with the repo live in [`notes/`](notes/) — e.g.
[runway overlay alignment](notes/runway-overlay-alignment.md) (why the
DCS-sourced runway overlay can look angled vs. the base map, and why it isn't a
bug).

## Building the Windows installer

Requires [Inno Setup 6](https://jrsoftware.org/isinfo.php) (`winget install JRSoftware.InnoSetup`) and the dev deps (`uv sync --all-extras`):

```powershell
scripts\build_windows.ps1 -Clean
```

Two stages — PyInstaller produces `packaging\dist\mizmap\` (one-folder bundle, ~65 MB), then Inno Setup wraps it as `packaging\dist\mizmap-setup-<version>.exe` (~26 MB compressed). See [packaging/mizmap.spec](packaging/mizmap.spec) and [packaging/mizmap.iss](packaging/mizmap.iss).

## License

MizMap is free software, licensed under the **GNU General Public License v3.0 or later** (GPL-3.0-or-later). See [LICENSE](LICENSE) for the full text.

Copyright (C) 2026 the MizMap authors.

- The vendored DCS-gRPC protobuf definitions (`proto/`, `mizmap/proto_gen/`) are derived from [DCS-gRPC/rust-server](https://github.com/DCS-gRPC/rust-server) and remain under **AGPL-3.0** ([LICENSES/AGPL-3.0.txt](LICENSES/AGPL-3.0.txt)); GPL-3.0 §13 expressly permits the combination.
- Bundled third-party libraries keep their own licenses — see [THIRD_PARTY_LICENSES.txt](THIRD_PARTY_LICENSES.txt) (regenerate with `scripts/gen_third_party_licenses.py` after changing dependencies).
- Map tiles © [OpenTopoMap](https://opentopomap.org) (CC-BY-SA); map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors (ODbL).
