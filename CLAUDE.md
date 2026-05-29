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
{ "type": "airbases_snapshot", "airbases": [<airbase>, ...] }
{ "type": "runways_snapshot", "runways": [<runway>, ...] }
{ "type": "navaids_snapshot", "navaids": [<navaid>, ...] }
{ "type": "marks_snapshot", "marks": [<mark>, ...] }
{ "type": "mark_added", "mark": <mark> }
{ "type": "mark_removed", "id": int }
{ "type": "fog_snapshot", "eval_ok": bool, "by_coalition": { "<coalition>": [<contact>, ...], ... } }
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

`<airbase>` = `{ name, callsign, display_name, coalition, category, lat, lon, alt, sidc }`. From `WorldService.GetAirbases` (standard RPC — no Eval). `category` is the DCS `AirbaseCategory` enum: 1=airdrome, 2=helipad (FARP/FOB/oil rig), 3=ship (carrier/LHA). `sidc` is a 2525C installation symbol computed by `mizmap/sidc.py:airbase_sidc_for` (airdrome/ship → airport `IBA---`; helipad → base `IB----`). Ships are sent for completeness but the frontend skips drawing them (carriers already render as live units). Same static lifecycle as routes/bullseyes (re-snapshot on (re)connect + `mission_start`; disconnect frame carries `"airbases": []`); coalition can flip on capture but we don't chase capture events. Frontend keys by `name`.

`<runway>` = `{ airbase_name, name, lat, lon, course, length_m, width_m }`. From `Airbase:getRunways()` via `CustomService.Eval` (so **Eval-gated**, like routes — empty without `evalEnabled = true`). `mizmap/runways.py` walks `world.getAirbases()` → `getRunways()` → `coord.LOtoLL`. `course` is the **true bearing in radians [0, 2π), already sign-corrected** — DCS returns a value whose sign is inverted vs a compass bearing, so we negate (verified against live Afghanistan: runway designators matched the negated heading — Farah `33`→330°, Kandahar `23`→234°). `name` is the runway designator normalized to a 2-char string ("18", "06"); DCS emits it as an integer. `length_m`/`width_m` in meters. Static lifecycle like routes; disconnect carries `"runways": []`. Frontend renders a cased line centered at `lat`/`lon` along `course` at true length, rides the **Airbases** layer toggle, and is coalition-independent (runways are physical terrain).

`<navaid>` = `{ name, type, callsign, lat, lon, freq_hz, channel, band }`. **No gRPC/Eval for the data** — parsed from the loaded theatre's on-disk `<dcs_install_dir>/Mods/terrains/<theatre>/beacons.lua` (`mizmap/navaids.py`, tolerant line parser), which carries `positionGeo` lat/lon directly. The theatre comes from `WorldService.GetTheatre`; the DCS path from the `dcs_install_dir` setting. `type` is a friendly category mapped from `BEACON_TYPE_*` (NDB, VOR, VOR/DME, DME, TACAN, VORTAC, RSBN, ILS-LOC/GS/OM/MM, PRMG-…). `freq_hz` is the carrier in Hz (NDB ~3e5, VOR ~1e8) or `null`; `channel` is the TACAN/VOR channel or `null`; `band` is the TACAN X/Y mode (so the frontend shows e.g. `75X`) — derived from the paired VHF freq (`.x00`→X, `.x50`→Y), defaulting to `X` for channel-only military TACANs (matching DCS), `null` when there's no channel. Static per theatre — re-resolved on (re)connect + `mission_start`, and **live on a `dcs_install_dir` Settings change** (no restart); disconnect carries `"navaids": []`. Frontend renders coalition-independent **filled bright-cyan glyphs** (white halo + dark outline) on a dedicated pane *below* the airbase symbols, on its own **Navaids** toggle; per-type glyph (hexagon=VOR family, triangle=TACAN/RSBN, square=DME, diamond=ILS/PRMG, filled circle=NDB), callsign/freq/channel in a hover tooltip. (Cyan, not chart-magenta: magenta was unreadable against DCS's reddish terrain + purple admin boundaries + red airport hatching — see the navaids journal.)

`<mark>` = `{ id, lat, lon, alt, text, coalition, group_id, time }`. `coalition` is `null` for marks visible to all, else 1/2/3; `group_id` is `null` for marks with no group restriction, else the DCS group id. `text` is the F10-map label (may be empty for player marks with no caption). `time` is seconds-since-mission-start when the mark was created. Snapshotted on (re)connect + on `mission_start`; delta-updated via `mark_added` (also used for change — upsert by id) and `mark_removed`. The rust-server emits `0xFFFFFFFF` as the sentinel for "no group restriction" — `mizmap/marks.py` collapses it to `null`. Visibility filtering (own-ship coalition + group) is performed on the frontend.

`fog_snapshot` carries the **fog-of-war detection picture** — what each coalition's sensors currently see — for the opt-in client-side viewpoint lens. `by_coalition` maps an *observer* coalition (string "1"/"2"/"3") to its detected `<contact>` = `{ id, visible, type_known, distance_known }`, where `id` joins against a live `<unit>` id (the frontend already has positions from `StreamUnits`, so only ids + knowledge flags ship). Built by `mizmap/fog.py`'s `CustomService.Eval` snippet, which unions `Controller.getDetectedTargets()` across every unit on each coalition (DCS exposes no coalition-level fog API; the per-unit-controller call is the only building block, and the detection-method enum is an *input* filter so we can't report *which* sensor). So it's **Eval-gated** like routes/runways — `eval_ok: false` means `evalEnabled = true` is missing (the frontend then shows a hint instead of hiding anything). **Unlike** the other layers it's **dynamic**: polled every ~1.5 s by a lifespan task in `server.py` (gated on ≥1 WS client; idles while disconnected), not fetched once. Disconnect/`mission_end` clear it (`by_coalition: {}`). The frontend (default **off**) hides non-viewpoint units that aren't detected, degrades symbology by confidence (type-unknown → bare affiliation frame; range-unknown → dashed uncertainty ring), and keeps fading grey **last-known ghosts** for a client-side memory window after contact is lost — **true coalition coloring is preserved** (a detected blue unit stays a blue frame even from the Red viewpoint; we don't flip affiliation to the observer's perspective, staying consistent with the rest of the map). Viewpoint defaults to own-ship coalition, overridable to Blue/Red/Neutral. The `id` join assumes `getDetectedTargets`' `object:getID()` matches the `StreamUnits` id — **confirmed against live DCS** (SCUD Alley / PersianGulf); `getDetectedTargets` can also return non-unit objects (weapons/statics) whose ids won't match any unit, which the frontend simply ignores. **Fidelity gaps (accepted):** detection is instantaneous (our memory window approximates DCS's own last-known persistence, doesn't mirror it); and a paused mission stalls the Eval like every other Eval RPC.

HTTP surfaces beyond the static frontend:
- `GET /api/elevation?lat=X&lon=Y` → `{ "elev_m": float | null }`. Calls `CustomService.Eval` with `coord.LLtoLO + land.getHeight` to return DCS terrain elevation at that point. Used by the click-to-measure BRA tool on the frontend. Requires `evalEnabled = true`.
- `GET /api/declination?lat=X&lon=Y[&alt=Z]` → `{ "declination_deg": float | null }`. Direct `CustomService.GetMagneticDeclination` RPC (no Eval — works without `evalEnabled`). Positive = easterly. Convert a true bearing to magnetic via `bearing_M = bearing_T - declination`. Used by the telemetry HUD (player heading) and the BRA tool (all three rows).
- `GET /api/settings` → `{ "settings": { <key>: { value, env_locked, restart_required } }, "dcs_install_dir_detected": str|null }`. Backs the in-app Settings panel. Editable keys: `http_host`, `http_port`, `grpc_host`, `grpc_port` (all `restart_required` — can't rebind a live socket) and `dcs_install_dir` (applies live). `value` for `dcs_install_dir` is the *explicit* override only (blank when relying on auto-detect; the detected path is the placeholder). `env_locked` is true when a `MIZMAP_*` var pins the key.
- `POST /api/settings` (body = any subset of the editable keys, as strings) → validates, writes `config.toml`, returns `{ "saved": bool, "restart_required": [keys], "errors": [...] }` (400 on validation failure). Env-pinned keys are rejected.
- `GET /tiles/{z}/{x}/{y}.png` → raster tile, served from the on-disk cache at `MIZMAP_TILE_CACHE_DIR` (default `./cache/tiles/`). On miss, fetched from `MIZMAP_TILE_URL` (the upstream public tile server), saved, then served. Frontend's `/api/config` now returns `/tiles/{z}/{x}/{y}.png` so the browser always goes through the proxy. Response header `X-Tile-Cache: hit|miss` for debugging. Wipe with `mizmap clear-cache`.

## Working rules (project-specific)

The user's global rules (`~/.claude/CLAUDE.md`) still apply: propose-before-code, no Co-Authored-By trailer, journal after work, `httpx` not `requests`, no mid-file imports.

Additions for this project:

- **Commit straight to `master`.** Solo project — no feature branches, no PRs, no merge commits. Ignore any generic "branch off the default branch first" habit; just commit to `master`. (Co-Authored-By trailer stays omitted, per the global rules.)
- **Phases are the unit of work.** Each phase opens with a written plan in chat (concrete deliverables, scope, smoke-test acceptance), then code, then a journal entry. Match the format of whatever earlier entries exist locally in `.journal/` (they may be absent on a fresh clone — see Catch up).
- **Tests count toward "done"** for backend changes that touch logic (`state.py`, `sidc.py`, future mission parsing). Pure plumbing changes (server wiring, frontend) don't need new tests.
- **Smoke-test before commit.** Standard recipe: `uv run python -m mizmap.dev.mock_server &` + `uv run mizmap serve &`, then inspect `/api/health` and the WS feed. Redirect output to a log file (`/tmp/mizmap-*.log` on Mac/Linux, `%TEMP%\mizmap\` on Windows).
- **`.journal/` is deliberately git-ignored** (see `.gitignore`) — decision history is kept **local to the maintainer's machine and intentionally unpublished**. This public repo was seeded fresh from a private one, dropping the old git history and leaving the journals behind on purpose. Keep writing journal entries (they're the local "why" record), but don't add `.journal/` to version control, and don't be surprised when a fresh clone has none.

## Operational gotchas

- **`evalEnabled = true` is required for mission routes** (and runways, elevation, and the fog-of-war lens). `mizmap/grpc_client.py:fetch_routes()` uses `CustomService.Eval` to walk the live `env.mission` table (DCS-gRPC 0.8.1 doesn't expose group routes via any standard RPC). The flag lives in `Saved Games/DCS/Config/dcs-grpc.lua`. Without it, Eval returns `FAILED_PRECONDITION` and the WS feed silently delivers an empty `mission_routes_snapshot` — visible as no polylines on the map. The fog lens detects this same `FAILED_PRECONDITION` and ships `fog_snapshot` with `eval_ok: false`, surfacing an in-panel "enable evalEnabled" hint rather than silently showing nothing. Restart DCS after toggling the config.
- **`mizmap/data/units.yaml` is the per-DCS-type authority** for refined SIDC symbology and SAM/AAA threat ranges. Schema is enforced strictly at import (bad entry kills `mizmap serve` startup with a clear error). Keys are DCS type strings exactly as they appear in `Unit.type`; the loader is in `mizmap/typedb.py`. Add entries freely — anything not listed falls back to the coarse coalition×category SIDC mapper with no threat ring.
- **A paused DCS mission stalls Eval-flavoured RPCs.** DCS suspends the Lua scripting environment while the mission is paused, so `CustomService.Eval` (used by `fetch_routes`, `fetch_elevation`, `fetch_runways` + the `fetch_fog_contacts` detection poll), `CustomService.GetMagneticDeclination`, and even `CoalitionService.GetBullseye` time out. The fog poll just times out per iteration (serialized awaits, no pileup) and the lens freezes on its last picture until unpause. `StreamUnits` also dries up — `/api/health` will show `units: 0` and the WS feed delivers nothing. If a restart cycle happens during pause, `state.routes` / `state.bullseyes` end up empty and stay that way until the next gRPC reconnect (browser refresh alone doesn't help — the WS snapshot reflects whatever state the server already holds). Recovery: unpause briefly to let the queries land, ideally before restarting `mizmap serve`.
- **Generated proto stubs** under `mizmap/proto_gen/` use absolute imports (`from dcs.common.v0 import common_pb2`). `mizmap/proto_gen/__init__.py` shims `sys.path` so they resolve without modifying generated files. Don't try to "fix" the import paths — regeneration will undo edits. **Corollary:** any module importing `dcs.*` must `import mizmap.proto_gen` *first*. `ruff check --fix` reorders that import below the `dcs.*` ones (isort third-party-before-first-party grouping) and breaks startup with `ModuleNotFoundError: No module named 'dcs'`. The repo deliberately keeps proto_gen-first and tolerates the resulting `I001` (also in `tests/test_marks.py`); CI runs only `pytest`, never ruff. So don't `ruff --fix` these files — restore proto_gen-first by hand if it happens.
- **Refresh protos** via `scripts/regen_protos.sh`. Update `proto/UPSTREAM.md` with the new upstream commit hash at the same time.
- **Mock vs real DCS** differs only by `MIZMAP_GRPC_HOST` / `MIZMAP_GRPC_PORT` env vars. Application code must never branch on "are we mocked." If you need scenario-specific behavior, extend the mock, don't fork the production path.
- **`grpc.aio.insecure_channel(...).channel_ready()` will succeed** if *anything* is listening on the port — including a stale orphan from a previous test. When debugging reconnect/disconnect behavior, verify port state with `lsof -i :50051`.
- **OpenTopoMap rate limits.** Mostly moot now since the local tile proxy + on-disk cache absorbs repeats. Still possible if you're panning over a fresh region — fallback is `MIZMAP_TILE_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` + `mizmap clear-cache` to flush the wrong-source tiles.
- **`config.toml` is now read in dev too** (was frozen-only), from `user_config_dir()` — `%APPDATA%\MizMap` when frozen, **cwd in dev**. It's gitignored. The in-app Settings panel (and `mizmap/config.py:update_config_file`) writes it. Precedence is unchanged: env (`MIZMAP_*`) > file > default/auto-detect. **Tests must isolate** by pointing `MIZMAP_CONFIG_FILE` at a tmp path (the default-asserting tests in `test_config.py` do this), else a stray repo-root `config.toml` would bend them. `dcs_install_dir` auto-detects via the registry (`HKCU\Software\Eagle Dynamics\DCS World*`) + common paths.

## Roadmap shorthand

- **Phase 0** ✅ scaffolding, mock harness, browser shell.
- **Phase 1** ✅ live unit tracking + MIL-STD-2525C symbology.
- **Phase 2** ✅ filter UI, mission waypoints/flight plan, telemetry HUD, bullseye + click-to-measure BRA tool, refined per-DCS-type SIDC, SAM/AAA threat rings. URL hash carries map view (pan/zoom).
- **Phase 3** ✅ twelve parts: magnetic bearings, mission-change auto-refresh, movement vectors, vertical speed, vector trails, local tile cache, interaction polish (sticky tooltips + middle-click measure + waypoint labels), configurable trail length, sticky-tooltip styling + waypoint-label collision declutter, responsive kneeboard layout, click-to-select unit + HUD redirect, units.yaml long-tail + case-insensitive lookup + port default 8766.
- **Phase 4 (packaging)** ✅ PyInstaller one-folder + Inno Setup per-user Windows installer. Tray icon (pystray), browser auto-open, `%APPDATA%\MizMap\config.toml`, `%LOCALAPPDATA%\MizMap\tiles\`. Build via `scripts/build_windows.ps1`. See [packaging/](packaging/) + Phase 4 journal.
- **Phase 5** ✅ own-ship awareness — auto-center on first own-ship sight + a Leaflet bottom-left recenter button. F10 map marks plumbed end-to-end (`WorldService.GetMarkPanels` snapshot + `mark_add`/`change`/`remove` events from `StreamEvents`); rendered client-side with own-ship coalition/group filtering. Navigation mode toggle: drag-aware map follow (drag breaks follow, recenter button re-engages) + top-center floating panel with next waypoint, magnetic bearing, distance, ETA. Mock now serves marks and emits add/remove cycles for dev testing.
- **Phase 6a** ✅ airbase layer — `WorldService.GetAirbases` → `airbases_snapshot` frame → 2525C installation symbols (airfields/FARPs) + name labels + `Airbases` filter toggle. Ships sent but not drawn (already live units). Mock serves 4 sample airbases.
- **Phase 6b** ✅ runways — `Airbase:getRunways()` via Eval → `runways_snapshot` → cased line per runway (true length, course-corrected) + tooltip (designator pair + heading + length). Rides the Airbases toggle, coalition-independent. Validated against a live Afghanistan A-10C mission (28 airbases / 26 runways; runway lines overlay the real strips on the topo base). Mock gained a minimal `CustomService.Eval` (canned runway JSON for the getRunways snippet).
- **Phase 7 (configuration UX)** ✅ in-app Settings panel (gear in the controls panel + tray "Settings…") backed by `GET/POST /api/settings`; `config.toml` now read+written in dev too (gitignored); new `dcs_install_dir` setting with registry/common-path auto-detect. Network settings are restart-required; the DCS path applies live. Built ahead of 6c, which needs the DCS install path.
- **Phase 6c** ✅ navaids (NDB/VOR/DME/TACAN/VORTAC/RSBN/ILS/PRMG) — parse the loaded theatre's on-disk `<dcs_install_dir>/Mods/terrains/<theatre>/beacons.lua` (uses `positionGeo` lat/lon directly — **no Eval/coordinate math**), keyed by `WorldService.GetTheatre`. `navaids_snapshot` frame; filled cyan glyphs (white halo) on their own Navaids toggle, drawn below airbase symbols; **live-applies** on a `dcs_install_dir` Settings change. Validated against live Afghanistan (49 navaids) + parser exercised on Caucasus (164). Mock `GetTheatre` returns Caucasus so navaids render offline on a DCS-installed box.
- **Phase 8 (fog of war)** ✅ opt-in viewpoint lens for mission designers — preview what a coalition would actually see under DCS's F10 "Fog of War." `mizmap/fog.py` unions `Controller.getDetectedTargets()` across each coalition via one `CustomService.Eval` (Eval-gated); dynamic `fog_snapshot` polled ~1.5 s by a `server.py` lifespan task. Frontend lens (default off): toggle + viewpoint (own-ship/Blue/Red/Neutral) + ghost-memory window; hides undetected non-viewpoint units, degrades symbology by detection confidence (type-unknown → bare affiliation frame, range-unknown → dashed uncertainty ring), fades grey last-known ghosts. True coalition coloring preserved (no observer-relative affiliation flip). Mock serves a time-varying detection picture. **Validated against live DCS** (SCUD Alley, PersianGulf, 109 units): the `getDetectedTargets` `object:getID()` ↔ `StreamUnits` id join holds — Blue detected 28 Reds (lens cut 109→34 visible: 28 Red + 6 Blue own), Red detected the Blue E-3A AWACS; threat rings of undetected SAMs correctly suppressed; one expected non-unit detection id (a weapon/static) harmlessly ignored. No name-join fallback needed.
- **Next** — mission replay, continued YAML long-tail.

## Environment & memory notes

- The user's per-project memory directory (`~/.claude/projects/.../memory/`) is **machine-local** and does not sync. Anything that needs to travel between machines must live in this repo — CLAUDE.md or code. (Journals do **not** travel: they're git-ignored — see Working rules.)
- Conversation transcripts and journals are both machine-local. Journals are the maintainer's local "why" record where they exist; the **cross-machine** record of what happened is commit messages + this file.

## When stuck or about to make a non-trivial decision

Ask. The user prefers explicit alignment over speculative refactors, and a written plan (even short) over silent action. The cost of a clarifying question is small; the cost of an unintended architecture drift is large.
