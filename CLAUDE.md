# MizMap — assistant context

This file briefs Claude Code sessions opened in this repo. It's read automatically at session start and travels with the repo between machines (the user's Mac dev box and Windows DCS PC).

## What this is

**MizMap** — a live moving-map viewer for **single-player** DCS World missions. Differentiator vs [DCS MovingMap](https://movingmap.bergison.com): the user chooses what's visible, rather than the tool enforcing the mission's in-game F10 view options.

See [README.md](README.md) for architecture diagram and run instructions.

## Catch up — read in this order

The journals, **where present**, contain decision history that code alone can't re-derive — authoritative for **why**; the code is authoritative for **what**. Note `.journal/` is deliberately git-ignored and was *not* published with this repo (see Working rules below), so on a fresh clone it's empty or absent. Read whatever is there locally; otherwise this file + README + the code are enough.

1. **Latest entry in [`.journal/`](.journal/)** — if present: current state, what just shipped, what's next.
2. [README.md](README.md) — quickstart + architecture.
3. Earlier entries in `.journal/` — archaeology, if present. Open for the rationale behind a surprising or stale decision.
4. [proto/UPSTREAM.md](proto/UPSTREAM.md) — vendored DCS-gRPC version.

## Locked decisions (don't drift without explicit user agreement)

- **Data source:** DCS-gRPC rust-server (consumed via `grpcio`).
- **Backend:** Python 3.11+, FastAPI + uvicorn, `typer` CLI.
- **Frontend:** vanilla JS + Leaflet + OpenTopoMap raster tiles.
- **Symbology:** MIL-STD-2525C via `milsymbol.js` (CDN). SIDC computed server-side.
- **Scope:** single-player only. Multiplayer is out of scope by design.
- **The map is the product.** MizMap exists so players don't have to switch to DCS's in-game F10 view. Any "alternate view" (kneeboard, second screen, etc.) keeps the live map as the centerpiece — only chrome adapts. A text-only info dashboard defeats the premise.

If you find yourself proposing to change any of these, treat it as a major decision — surface the trade-off, ask, don't just refactor.

## WebSocket message contract (frozen)

Any change to message shapes must be a deliberate, user-agreed decision — not an accidental drift during a refactor.

```
{ "type": "hello", "version": "0.0.1" }
{ "type": "grpc_status", "connected": bool, "host": str, "error": str|null }
{ "type": "units_snapshot", "units": [<unit>, ...] }
{ "type": "unit_update", "unit": <unit> }
{ "type": "unit_gone", "id": int }
{ "type": "mission_routes_snapshot", "routes": [<route>, ...] }
{ "type": "bullseyes_snapshot", "bullseyes": [<bullseye>, ...] }
{ "type": "marks_snapshot", "marks": [<mark>, ...] }
{ "type": "mark_added", "mark": <mark> }
{ "type": "mark_removed", "id": int }
```

`<unit>` = `{ id, name, callsign, type, coalition, group: {id, name, category}, lat, lon, alt, heading, speed, track, vs, player_name, sidc, threat_km }`.
- `coalition`: 1=neutral, 2=red, 3=blue (DCS enum).
- `group.category`: 1=airplane, 2=helo, 3=ground, 4=ship, 5=train.
- `heading`: nose direction, radians, normalized to `[0, 2π)`. From `Orientation.heading`. HUD/HSI reads.
- `track`: motion direction, radians, normalized to `[0, 2π)`. Computed as `atan2(velocity.z, velocity.x)` — `Velocity.heading` is broken in DCS-gRPC 0.8.1 (see Phase 3 movement-vectors journal for the trail of empirical evidence).
- `speed`: m/s, horizontal ground speed.
- `vs`: vertical speed, m/s, signed (positive = climb). From `Velocity.velocity.y` (+y = up).
- `player_name`: string when a player controls this unit, `null` otherwise. Used by the telemetry HUD as own-ship.
- `sidc`: 15-char MIL-STD-2525C, computed by `mizmap/sidc.py`. Per-type refinement via `mizmap/data/units.yaml` (loaded by `mizmap/typedb.py`); coarse `(coalition, category)` fallback for unknown types.
- `threat_km`: SAM/AAA max engagement range in km, or `null`. From `mizmap/data/units.yaml`.

`<route>` = `{ group_id, group_name, coalition, category, points: [<point>, ...] }`, with `<point>` = `{ lat, lon, alt, type, action, speed, eta, name }`. `type`/`action` are raw .miz strings; `speed` is m/s; `eta` is seconds from mission start; `name` is the .miz waypoint name (often empty — frontend falls back to `WP N`). Routes are static for the mission — re-snapshotted on (re)connect or disconnect (disconnect frame carries `"routes": []`); no update/delta messages.

`<bullseye>` = `{ coalition, lat, lon, alt }`. 0–2 entries (one per coalition with a bullseye in the .miz). Same static lifecycle as routes.

`<mark>` = `{ id, lat, lon, alt, text, coalition, group_id, time }`. `coalition` is `null` for marks visible to all, else 1/2/3; `group_id` is `null` for marks with no group restriction, else the DCS group id. `text` is the F10-map label (may be empty for player marks with no caption). `time` is seconds-since-mission-start when the mark was created. Snapshotted on (re)connect + on `mission_start`; delta-updated via `mark_added` (also used for change — upsert by id) and `mark_removed`. The rust-server emits `0xFFFFFFFF` as the sentinel for "no group restriction" — `mizmap/marks.py` collapses it to `null`. Visibility filtering (own-ship coalition + group) is performed on the frontend.

HTTP surfaces beyond the static frontend:
- `GET /api/elevation?lat=X&lon=Y` → `{ "elev_m": float | null }`. Calls `CustomService.Eval` with `coord.LLtoLO + land.getHeight` to return DCS terrain elevation at that point. Used by the click-to-measure BRA tool on the frontend. Requires `evalEnabled = true`.
- `GET /api/declination?lat=X&lon=Y[&alt=Z]` → `{ "declination_deg": float | null }`. Direct `CustomService.GetMagneticDeclination` RPC (no Eval — works without `evalEnabled`). Positive = easterly. Convert a true bearing to magnetic via `bearing_M = bearing_T - declination`. Used by the telemetry HUD (player heading) and the BRA tool (all three rows).
- `GET /tiles/{z}/{x}/{y}.png` → raster tile, served from the on-disk cache at `MIZMAP_TILE_CACHE_DIR` (default `./cache/tiles/`). On miss, fetched from `MIZMAP_TILE_URL` (the upstream public tile server), saved, then served. Frontend's `/api/config` now returns `/tiles/{z}/{x}/{y}.png` so the browser always goes through the proxy. Response header `X-Tile-Cache: hit|miss` for debugging. Wipe with `mizmap clear-cache`.

## Working rules (project-specific)

The user's global rules (`~/.claude/CLAUDE.md`) still apply: propose-before-code, no Co-Authored-By trailer, journal after work, `httpx` not `requests`, no mid-file imports.

Additions for this project:

- **Phases are the unit of work.** Each phase opens with a written plan in chat (concrete deliverables, scope, smoke-test acceptance), then code, then a journal entry. Match the format of whatever earlier entries exist locally in `.journal/` (they may be absent on a fresh clone — see Catch up).
- **Tests count toward "done"** for backend changes that touch logic (`state.py`, `sidc.py`, future mission parsing). Pure plumbing changes (server wiring, frontend) don't need new tests.
- **Smoke-test before commit.** Standard recipe: `uv run python -m mizmap.dev.mock_server &` + `uv run mizmap serve &`, then inspect `/api/health` and the WS feed. Redirect output to a log file (`/tmp/mizmap-*.log` on Mac/Linux, `%TEMP%\mizmap\` on Windows).
- **`.journal/` is deliberately git-ignored** (see `.gitignore`) — decision history is kept **local to the maintainer's machine and intentionally unpublished**. This public repo was seeded fresh from a private one, dropping the old git history and leaving the journals behind on purpose. Keep writing journal entries (they're the local "why" record), but don't add `.journal/` to version control, and don't be surprised when a fresh clone has none.

## Operational gotchas

- **`evalEnabled = true` is required for mission routes.** `mizmap/grpc_client.py:fetch_routes()` uses `CustomService.Eval` to walk the live `env.mission` table (DCS-gRPC 0.8.1 doesn't expose group routes via any standard RPC). The flag lives in `Saved Games/DCS/Config/dcs-grpc.lua`. Without it, Eval returns `FAILED_PRECONDITION` and the WS feed silently delivers an empty `mission_routes_snapshot` — visible as no polylines on the map. Restart DCS after toggling the config.
- **`mizmap/data/units.yaml` is the per-DCS-type authority** for refined SIDC symbology and SAM/AAA threat ranges. Schema is enforced strictly at import (bad entry kills `mizmap serve` startup with a clear error). Keys are DCS type strings exactly as they appear in `Unit.type`; the loader is in `mizmap/typedb.py`. Add entries freely — anything not listed falls back to the coarse coalition×category SIDC mapper with no threat ring.
- **A paused DCS mission stalls Eval-flavoured RPCs.** DCS suspends the Lua scripting environment while the mission is paused, so `CustomService.Eval` (used by `fetch_routes` + `fetch_elevation`), `CustomService.GetMagneticDeclination`, and even `CoalitionService.GetBullseye` time out. `StreamUnits` also dries up — `/api/health` will show `units: 0` and the WS feed delivers nothing. If a restart cycle happens during pause, `state.routes` / `state.bullseyes` end up empty and stay that way until the next gRPC reconnect (browser refresh alone doesn't help — the WS snapshot reflects whatever state the server already holds). Recovery: unpause briefly to let the queries land, ideally before restarting `mizmap serve`.
- **Generated proto stubs** under `mizmap/proto_gen/` use absolute imports (`from dcs.common.v0 import common_pb2`). `mizmap/proto_gen/__init__.py` shims `sys.path` so they resolve without modifying generated files. Don't try to "fix" the import paths — regeneration will undo edits.
- **Refresh protos** via `scripts/regen_protos.sh`. Update `proto/UPSTREAM.md` with the new upstream commit hash at the same time.
- **Mock vs real DCS** differs only by `MIZMAP_GRPC_HOST` / `MIZMAP_GRPC_PORT` env vars. Application code must never branch on "are we mocked." If you need scenario-specific behavior, extend the mock, don't fork the production path.
- **`grpc.aio.insecure_channel(...).channel_ready()` will succeed** if *anything* is listening on the port — including a stale orphan from a previous test. When debugging reconnect/disconnect behavior, verify port state with `lsof -i :50051`.
- **OpenTopoMap rate limits.** Mostly moot now since the local tile proxy + on-disk cache absorbs repeats. Still possible if you're panning over a fresh region — fallback is `MIZMAP_TILE_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` + `mizmap clear-cache` to flush the wrong-source tiles.

## Roadmap shorthand

- **Phase 0** ✅ scaffolding, mock harness, browser shell.
- **Phase 1** ✅ live unit tracking + MIL-STD-2525C symbology.
- **Phase 2** ✅ filter UI, mission waypoints/flight plan, telemetry HUD, bullseye + click-to-measure BRA tool, refined per-DCS-type SIDC, SAM/AAA threat rings. URL hash carries map view (pan/zoom).
- **Phase 3** ✅ twelve parts: magnetic bearings, mission-change auto-refresh, movement vectors, vertical speed, vector trails, local tile cache, interaction polish (sticky tooltips + middle-click measure + waypoint labels), configurable trail length, sticky-tooltip styling + waypoint-label collision declutter, responsive kneeboard layout, click-to-select unit + HUD redirect, units.yaml long-tail + case-insensitive lookup + port default 8766.
- **Phase 4 (packaging)** ✅ PyInstaller one-folder + Inno Setup per-user Windows installer. Tray icon (pystray), browser auto-open, `%APPDATA%\MizMap\config.toml`, `%LOCALAPPDATA%\MizMap\tiles\`. Build via `scripts/build_windows.ps1`. See [packaging/](packaging/) + Phase 4 journal.
- **Phase 5** ✅ own-ship awareness — auto-center on first own-ship sight + a Leaflet bottom-left recenter button. F10 map marks plumbed end-to-end (`WorldService.GetMarkPanels` snapshot + `mark_add`/`change`/`remove` events from `StreamEvents`); rendered client-side with own-ship coalition/group filtering. Navigation mode toggle: drag-aware map follow (drag breaks follow, recenter button re-engages) + top-center floating panel with next waypoint, magnetic bearing, distance, ETA. Mock now serves marks and emits add/remove cycles for dev testing.
- **Next** — mission replay, continued YAML long-tail.

## Environment & memory notes

- The user's per-project memory directory (`~/.claude/projects/.../memory/`) is **machine-local** and does not sync. Anything that needs to travel between machines must live in this repo — CLAUDE.md or code. (Journals do **not** travel: they're git-ignored — see Working rules.)
- Conversation transcripts and journals are both machine-local. Journals are the maintainer's local "why" record where they exist; the **cross-machine** record of what happened is commit messages + this file.

## When stuck or about to make a non-trivial decision

Ask. The user prefers explicit alignment over speculative refactors, and a written plan (even short) over silent action. The cost of a clarifying question is small; the cost of an unintended architecture drift is large.
