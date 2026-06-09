// MizMap browser viewer.
// Phase 1: render mission units as MIL-STD-2525C symbols on the Leaflet map.

const versionEl = document.getElementById("versionLabel");
const wsStatusEl = document.getElementById("wsStatus");
const grpcStatusEl = document.getElementById("grpcStatus");
const grpcErrorEl = document.getElementById("grpcError");
const telemetryEl = document.getElementById("telemetry");
const tlmEls = {
    name: document.getElementById("tlmName"),
    lat: document.getElementById("tlmLat"),
    lon: document.getElementById("tlmLon"),
    mgrs: document.getElementById("tlmMgrs"),
    alt: document.getElementById("tlmAlt"),
    gs: document.getElementById("tlmGs"),
    vs: document.getElementById("tlmVs"),
    hdg: document.getElementById("tlmHdg"),
};

const M_PER_S_TO_KTS = 1.94384;
const M_PER_S_TO_FT_PER_MIN = 196.85; // m/s → ft/min = × 60 × 3.28084
const M_TO_FT = 3.28084;
const M_TO_NM = 1 / 1852;
const MGRS_ACCURACY = 4; // 4 → 10m precision, easy to read off a moving aircraft
// "Cased" line style — dark underlay so the colored line reads against any
// base-map background (light hills, water, snow, etc).
const CASING_COLOR = "#000";
const CASING_OPACITY = 0.85;

const measureEl = document.getElementById("measure");
const measureBullEl = document.getElementById("measureBull");
const measureBullLabelEl = document.getElementById("measureBullLabel");
const measureBullRowEl = document.getElementById("measureBullRow");
const measureSelfOutEl = document.getElementById("measureSelfOut");
const measureSelfOutRowEl = document.getElementById("measureSelfOutRow");
const measureSelfInEl = document.getElementById("measureSelfIn");
const measureSelfInRowEl = document.getElementById("measureSelfInRow");
const measureAltEl = document.getElementById("measureAlt");
const measureGridEl = document.getElementById("measureGrid");
const measureGridRowEl = document.getElementById("measureGridRow");
const measureLatLonEl = document.getElementById("measureLatLon");
const measureLatLonRowEl = document.getElementById("measureLatLonRow");
const measureClearBtn = document.getElementById("measureClear");
const measureHintEl = document.getElementById("measureHint");
const MEASURE_SELF_COLOR = "#f4d35e";

const cursorReadoutEl = document.getElementById("cursorReadout");
const cursorMgrsEl = document.getElementById("cursorMgrs");
const cursorLatLonEl = document.getElementById("cursorLatLon");

const CAUCASUS_CENTER = [43.0, 40.8]; // ~midpoint of the DCS Caucasus theater
// Default zoom when auto-centering on first sight of the player's own-ship.
// 12 is roughly "regional" — ~ a 20 km × 15 km window in mid-latitudes,
// enough to see nearby waypoints and threat rings without panning.
const OWN_SHIP_INITIAL_ZOOM = 12;
// Window for distinguishing a single from a double click on the recenter
// button — a lone click's action fires after this delay; a second click within
// it is a double-click and cancels the pending single.
const RECENTER_DBLCLICK_MS = 250;
const SYMBOL_SIZE = 28; // px, rendered by milsymbol
const WAYPOINT_RADIUS = 4; // px
const ROUTE_WEIGHT = 2; // px
const COALITION_COLOR = { 1: "#9aa0a6", 2: "#e07c7c", 3: "#5b8def" }; // neutral, red, blue

// Movement vectors — a fixed-length stub from the unit symbol along its track,
// sized at 2× the symbol. Direction only: length no longer encodes speed, since
// speed-scaled projections spanned half the map for fast movers. Held constant
// in screen pixels (zoom-invariant), so endpoints are recomputed on zoomend.
const VECTOR_LENGTH_PX = SYMBOL_SIZE * 2; // 56 px
const VECTOR_MIN_SPEED_MS = 1.0; // ~2 kts — anything slower is noise/stationary
const VECTOR_WEIGHT = 2;
const EARTH_RADIUS_M = 6371000;

// Trails — ring buffer of recent positions, rendered as N segments of stepped
// opacity for a fade-out effect. Buffer is per-session client state; full
// snapshot replaces (mission change) tear down all trails. The buffer cap is
// the longest selectable length so increasing the display length immediately
// reveals existing history rather than waiting for the buffer to fill.
const TRAIL_LENGTHS_SEC = [15, 30, 60, 120, 300]; // discrete choices; ≈ positions at 1 Hz updates
const TRAIL_LENGTH_DEFAULT_SEC = 60;
const TRAIL_BUFFER_MAX = Math.max(...TRAIL_LENGTHS_SEC);
const TRAIL_SEGMENTS = 5;
const TRAIL_WEIGHT = 3;
const TRAIL_OPACITY_NEWEST = 0.95;
const TRAIL_OPACITY_OLDEST = 0.30;
const TRAIL_LS_KEY = "mizmap.trailLengthSec";
// Route display mode: "focus" (own-ship + selected unit's group only, the
// default — busy missions drown the map in polylines) or "all".
const ROUTES_MODE_DEFAULT = "focus";
const ROUTES_MODES = ["focus", "all"];
const ROUTES_MODE_LS_KEY = "mizmap.routesMode";
// Collapsed/expanded state of the filter-panel disclosure sections, keyed by
// the section's data-section value. HTML sets the smart defaults (Basemap +
// Fog of war collapsed); a saved entry overrides per section.
const SECTIONS_LS_KEY = "mizmap.sections";

// Navigation mode — when on, the map follows the player and a panel shows
// route metrics for the next waypoint. Persisted across reloads.
const NAV_LS_KEY = "mizmap.navMode";
// Below this ground speed the ETA reads "--:--" rather than swinging wildly.
// ~5 m/s ≈ 10 kts: not actually moving for nav purposes.
const NAV_ETA_MIN_SPEED_MS = 5.0;

// Fog of war — an opt-in viewpoint lens. When on, non-viewpoint coalitions are
// shown only where the viewpoint's sensors have detected them (server-side
// getDetectedTargets union, delivered as fog_snapshot). Detection confidence
// degrades the symbol: type-unknown → bare affiliation frame, range-unknown →
// dashed uncertainty ring; a lost contact lingers as a fading grey "last-known"
// ghost for the memory window, then disappears. Default OFF — it's a deliberate
// constraint the user opts into, not the mission's enforced F10 view.
const FOG_MEMORY_CHOICES = [0, 30, 60, 120, 300]; // seconds; 0 = no ghosts
const FOG_MEMORY_DEFAULT_SEC = 60;
const FOG_TICK_MS = 1000; // cadence for re-fading/aging ghosts between snapshots
const FOG_GHOST_OPACITY_MAX = 0.7; // freshly-lost ghost
const FOG_GHOST_OPACITY_MIN = 0.2; // about to age out of the memory window
const FOG_GHOST_COLOR = "#9aa0a6"; // grey monochrome for last-known symbols
const FOG_RING_RADIUS_M = 3000; // dashed "position uncertain" ring (range unknown)
const FOG_RING_COLOR = "#d8b45a";

const unitsById = new Map(); // id -> { marker, data, visible }
const routesByGroupId = new Map(); // group_id -> { layer: L.LayerGroup, data, visible }
const bullseyesByCoalition = new Map(); // coalition -> { marker, data, visible }
const airbasesByName = new Map(); // name -> { layer: L.LayerGroup, data, visible }
const runwaysByKey = new Map(); // key -> { layer: L.LayerGroup, data, visible }
const runwaysByAirbase = new Map(); // airbase_name -> [<runway>, ...] (for the airbase tooltip)
const navaidsByKey = new Map(); // key -> { marker, data, visible }
const marksById = new Map(); // id -> { marker, data, visible }

// Fog-of-war runtime state. `fogContacts`: latest server snapshot keyed by
// observer coalition (string) -> [{id, visible, type_known, distance_known}].
// `fogMemory`: per-unit last-known detection for the ACTIVE viewpoint only
// (cleared when the viewpoint changes) -> { rec, lastSeen(ms), gen }.
// `fogPollGen` stamps "this snapshot"; a unit whose memory entry predates the
// latest poll is a lost contact (ghost) rather than currently detected.
let fogContacts = {};
let fogEvalOk = true;
let fogReceived = false; // gate hiding until the first fog_snapshot lands
let fogPollGen = 0;
const fogMemory = new Map();

// DCS AirbaseCategory enum. Ships (carriers/LHAs) already render as live units
// via StreamUnits, so the airbase layer skips them to avoid double symbols.
const AIRBASE_CATEGORY_SHIP = 3;
const AIRBASE_CAT_NAMES = { 1: "Airfield", 2: "FARP", 3: "Ship" };
// Runways are coalition-neutral terrain — light grey, ride the Airbases toggle.
const RUNWAY_COLOR = "#e6e6e6";
const RUNWAY_WEIGHT = 4;
// Schematic dashed treatment: a thin dashed centerline reads as a data
// annotation rather than a second (slightly-tilted) runway, so the small
// DCS-vs-basemap orientation gap stops clashing with the strip underneath.
// Opacity is zoom-driven (applyRunwayFade) — full when zoomed out for
// orientation, faded as you zoom in, where the base map shows the real runway.
const RUNWAY_LINE_WEIGHT = 1.75;
const RUNWAY_CASING_WEIGHT = 3; // thin halo for legibility on any base-map tone
const RUNWAY_DASH = "3 6";
const RUNWAY_FADE_ZOOM_FULL = 11; // ≤ here: full opacity
const RUNWAY_FADE_ZOOM_MIN = 15; // ≥ here: faded out (base map shows the strip)
const RUNWAY_BASE_OPACITY = 0.9;
const RUNWAY_MIN_OPACITY = 0.12;
const RUNWAY_CASING_RATIO = 0.45; // casing stays subordinate to the dashed line
// Navaids — bright cyan FILLED glyphs with a white halo + dark outline. Chart
// magenta was unreadable against DCS terrain (reddish mountains, purple admin
// boundaries, red airport hatching all clash); cyan is the complementary pop
// and stays distinct from the coalition colors. Filled (not hollow) + haloed so
// the small glyphs read on any base-map tone. Own pane below the airbase markers
// so a co-located beacon reads as a separate chart layer.
const NAVAID_FILL = "#19dfe6"; // bright cyan
const NAVAID_OUTLINE = "#06343a"; // dark edge for definition on light terrain
const NAVAID_HALO = "#ffffff"; // ring for separation on busy/dark areas
const NAVAID_SIZE = 20;
const NAVAIDS_PANE = "dcmNavaidsPane";
const NAVAIDS_PANE_Z = 450; // above tiles/runways (overlayPane 400), below markers (600)

// F10 map marks rendering — match DCS's small red-bordered circles. Fixed
// pixel size (circleMarker, not circle) so they don't scale with zoom.
const MARK_RADIUS_PX = 14;
const MARK_BORDER_WEIGHT = 2.5;
const MARK_BORDER_COLOR = "#ff3b30";
const MARK_FILL_COLOR = "#ff3b30";
const MARK_FILL_OPACITY = 0.15;
// Marks render on a custom pane above the default markerPane (z=600) so they
// aren't occluded by unit icons stacked on top. Below tooltipPane (z=650) so
// tooltips still draw above. The SVG renderer is dedicated to that pane.
const MARKS_PANE = "dcmMarksPane";
const MARKS_PANE_Z = 610;
let marksRenderer = null;
let map; // Leaflet map, assigned once
// Currently-selected unit id, or null = no selection (HUD falls back to the
// player's own ship). Set by clicking a unit symbol; cleared by clicking the
// same one again or when the unit disappears. Mutually exclusive — selecting
// a different unit deselects the previous one.
let selectedUnitId = null;
// { lat, lon, marker, elevReqId, layers, elevM, declinationDeg } when active.
// `layers` is the L.LayerGroup holding lines + on-line labels for the current
// measurement. `elevM` and `declinationDeg` come from parallel HTTP fetches
// that resolve after the click and update the panel in place. `declinationDeg
// === null` means "use true bearings" (either still fetching or fetch failed).
// `mode` is "tracking" (target follows the cursor live; no Eval fetches, so
// bearings stay true) or "frozen" (locked at the click point; elevation +
// declination fetched, so bearings refine to magnetic where available).
let measureState = null;
let measureReqCounter = 0; // monotonic id so stale elevation responses are dropped
let measureRebuildRaf = 0; // pending rAF id coalescing per-cursor-move rebuilds

// Cached magnetic declination at the player's current position. Refetched at
// most every 30 s (declination changes <0.01°/min even at jet speeds, so a
// half-minute cadence is way over the precision floor). `value === null` means
// "unknown — display as °T". Survives player slot changes.
const playerDecState = { value: null, fetchedAt: 0 };
const PLAYER_DEC_REFRESH_MS = 30000;

// --- filter state -----------------------------------------------------------
// Bookmarkable via URL hash: #coal=brn&cat=ahgst&layers=r (omitted letters = filtered out).
// AND-logic: a unit shows only if BOTH its coalition AND its category are enabled.
// All-on is the default and produces an empty hash for a clean URL.
const HASH_COAL = { 1: "n", 2: "r", 3: "b" }; // DCS Coalition enum
// GroupCategory enum. Train (5) is folded into Ground (3) — see shouldShow —
// so it has no chip and no hash letter of its own.
const HASH_CAT = { 1: "a", 2: "h", 3: "g", 4: "s" };
const HASH_LAYER = { routes: "r", bullseyes: "b", airbases: "f", navaids: "n", marks: "k", measure: "m", threats: "t", vectors: "v", trails: "l" };
const FILTERS = {
    coalition: { 1: true, 2: true, 3: true },
    category: { 1: true, 2: true, 3: true, 4: true },
    layers: { routes: true, bullseyes: true, airbases: true, navaids: true, marks: true, measure: true, threats: true, vectors: true, trails: true },
    trailLengthSec: TRAIL_LENGTH_DEFAULT_SEC,
    // Lives outside `layers` (like trailLengthSec) so the all-layers-on →
    // empty-hash invariant is untouched. "focus" = own-ship + selected only.
    routesMode: ROUTES_MODE_DEFAULT,
    // Fog lens is its own slice (default off) rather than a `layers` flag so it
    // stays out of the all-layers-on→empty-hash invariant. viewpoint: "auto"
    // (own ship) | "1"|"2"|"3" (neutral/red/blue). memorySec: ghost window.
    fog: { on: false, viewpoint: "auto", memorySec: FOG_MEMORY_DEFAULT_SEC },
};
const N_CAT_FLAGS = Object.keys(HASH_CAT).length;
const N_LAYER_FLAGS = Object.keys(HASH_LAYER).length;
// Set by decodeHash when the URL carries `trail=`. Init uses it to decide
// whether to fall back to localStorage (hash wins; localStorage is the
// remembered preference for hash-less loads).
let trailLengthSetByHash = false;
// Same hash-wins dance for `routes=` (route display mode).
let routesModeSetByHash = false;
// Map view (center + zoom). Populated by decodeHash on load and used as the
// initial view by buildMap; thereafter re-emitted on every Leaflet `moveend`.
let pendingView = null;
// True once we've auto-centered on the player's own-ship (or skipped doing so
// because the URL hash already carried a view). Prevents repeated snaps on
// every unit_update once the player appears.
let initialOwnShipCenterDone = false;
// Basemap selection. `basemapList`/`defaultBasemapId` come from /api/config;
// `activeBasemapId` is the rendered one; `basemapLayer` is its Leaflet layer.
// `pendingBasemap` is set by decodeHash from `base=` (hash wins over default).
let basemapList = [];
let defaultBasemapId = null;
let activeBasemapId = null;
let basemapLayer = null;
let pendingBasemap = null;
// Leaflet control wrapper for the recenter button — instantiated by buildMap;
// shown when the player's own-ship is on the map, hidden otherwise.
let recenterControl = null;
// Navigation mode toggle. When on, the nav panel shows next-waypoint metrics
// and turning it on engages map-follow of the own-ship (via followedUnitId).
let navModeOn = false;
// The unit the map continuously re-centers on (null = not following) — the
// single source of truth for map-follow, shared by the recenter button and nav
// mode. Set by: the recenter button (single-click → selected unit, double-click
// → own-ship) and nav-on (→ own-ship). Cleared by: toggling follow off,
// deselecting / switching the selected unit, a user drag, the followed unit
// disappearing, or a mission/snapshot reset. Never persisted — a reload comes
// back not-following.
let followedUnitId = null;
// Manual override for the displayed waypoint index. `null` = use the auto
// heuristic (closest ahead). Set by the prev/next arrow buttons; reset when
// nav-mode is turned off or when routes change (mission reload).
let navWpIndexOverride = null;

function shouldShow(u) {
    if (FILTERS.coalition[u.coalition] !== true) return false;
    // Trains (category 5) have no chip of their own — they ride the Ground (3)
    // filter, since a train is a surface/land unit.
    const cat = u.group.category === 5 ? 3 : u.group.category;
    if (FILTERS.category[cat] !== true) return false;
    return fogVisInfo(u).show;
}

function shouldShowRoute(r) {
    // Routes track the coalition filter; layer toggle is the master switch.
    if (FILTERS.layers.routes !== true) return false;
    if (FILTERS.coalition[r.coalition] !== true) return false;
    if (FILTERS.routesMode === "all") return true;
    // "focus" (default): only the own-ship group's route and the selected
    // unit's group route survive — full route clutter on busy missions is
    // opt-in. Routes are group-level, so selecting any unit of a group
    // shows that group's plan. No own-ship and no selection → no routes.
    const player = findPlayerUnit();
    if (player && r.group_id === player.group.id) return true;
    if (selectedUnitId !== null) {
        const sel = unitsById.get(selectedUnitId);
        if (sel && r.group_id === sel.data.group.id) return true;
    }
    return false;
}

function shouldShowBullseye(b) {
    return FILTERS.layers.bullseyes === true && FILTERS.coalition[b.coalition] === true;
}

function shouldShowMark(m) {
    if (FILTERS.layers.marks !== true) return false;
    // Coalition is the only restriction we apply. Group-restriction is left
    // out deliberately — campaign/mission scripts often address marks to
    // specific groups for AI use, and in single-player we want the player to
    // see those for situational awareness even when not in that group.
    // No own-ship → show everything we have.
    const player = findPlayerUnit();
    if (!player) return true;
    if (m.coalition !== null && m.coalition !== player.coalition) return false;
    return true;
}

function shouldShowAirbase(a) {
    // Carriers/LHAs (ship category) already render as live units — skip them
    // here. Airfields/FARPs track the coalition filter like routes/bullseyes.
    if (FILTERS.layers.airbases !== true) return false;
    if (a.category === AIRBASE_CATEGORY_SHIP) return false;
    return FILTERS.coalition[a.coalition] === true;
}

function shouldShowThreat(u) {
    return (
        FILTERS.layers.threats === true &&
        FILTERS.coalition[u.coalition] === true &&
        typeof u.threat_km === "number" &&
        u.threat_km > 0 &&
        // Under fog, a threat ring only shows while the unit is actively
        // detected — a lost (ghost) or never-seen SAM mustn't leak its range.
        fogVisInfo(u).live
    );
}

// --- fog of war (viewpoint lens) --------------------------------------------
// fogVisInfo(u) is the single source of truth for a unit's fog state. It's
// consulted by every visibility predicate, so it must stay cheap (map lookups).
// `show` gates the symbol; `live` (currently detected, not a ghost) gates the
// derived layers (threats/vectors/trails); `ghost`/`typeKnown`/`distanceUnknown`
// /`opacity` drive degraded rendering. When the lens is inactive everything is
// fully visible — fog never *adds* visibility, only subtracts it.
const FOG_VIS_FULL = Object.freeze({ show: true, live: true, ghost: false, typeKnown: true, distanceUnknown: false, opacity: 1 });
const FOG_VIS_HIDDEN = Object.freeze({ show: false, live: false, ghost: false, typeKnown: false, distanceUnknown: false, opacity: 0 });

function activeViewpointCoalition() {
    if (FILTERS.fog.viewpoint === "auto") {
        const p = findPlayerUnit();
        return p ? p.coalition : null;
    }
    const n = parseInt(FILTERS.fog.viewpoint, 10);
    return Number.isInteger(n) ? n : null;
}

// The lens only filters once it has real data AND a resolvable viewpoint AND
// detection is actually available (eval enabled). Otherwise it's a no-op so the
// map never silently blanks (e.g. before the first snapshot, or auto-viewpoint
// with no own-ship yet) — the "enable evalEnabled" hint covers the eval case.
function fogActive() {
    return FILTERS.fog.on && fogReceived && fogEvalOk && activeViewpointCoalition() !== null;
}

function fogVisInfo(u) {
    if (!fogActive()) return FOG_VIS_FULL;
    const vp = activeViewpointCoalition();
    if (u.coalition === vp) return FOG_VIS_FULL; // own side is always fully visible
    const mem = fogMemory.get(u.id);
    if (!mem) return FOG_VIS_HIDDEN; // never detected by this viewpoint
    if (mem.gen === fogPollGen) {
        // Currently detected in the latest poll.
        return {
            show: true,
            live: true,
            ghost: false,
            typeKnown: !!mem.rec.type_known,
            distanceUnknown: !mem.rec.distance_known,
            opacity: 1,
        };
    }
    // Lost contact — fade a last-known ghost over the memory window.
    const memMs = FILTERS.fog.memorySec * 1000;
    if (memMs <= 0) return FOG_VIS_HIDDEN;
    const ageMs = Date.now() - mem.lastSeen;
    if (ageMs > memMs) return FOG_VIS_HIDDEN;
    const fade = 1 - ageMs / memMs; // 1 (fresh) → 0 (about to expire)
    return {
        show: true,
        live: false,
        ghost: true,
        typeKnown: !!mem.rec.type_known,
        distanceUnknown: false,
        opacity: FOG_GHOST_OPACITY_MIN + (FOG_GHOST_OPACITY_MAX - FOG_GHOST_OPACITY_MIN) * fade,
    };
}

// Fold the latest fog_snapshot into per-unit memory for the active viewpoint.
function ingestFog() {
    const vp = activeViewpointCoalition();
    if (vp === null) return;
    fogPollGen++;
    const now = Date.now();
    const list = fogContacts[String(vp)] || [];
    for (const rec of list) {
        if (typeof rec.id !== "number") continue;
        fogMemory.set(rec.id, { rec, lastSeen: now, gen: fogPollGen });
    }
    // Prune contacts that are gone AND past the memory window (or memory off).
    const memMs = FILTERS.fog.memorySec * 1000;
    for (const [id, mem] of fogMemory) {
        if (mem.gen !== fogPollGen && (memMs <= 0 || now - mem.lastSeen > memMs)) {
            fogMemory.delete(id);
        }
    }
}

// Viewpoint (or enable) changed — the previous observer's memory is meaningless
// for the new one, so drop it and rebuild from the freshest snapshot.
function resetFogViewpoint() {
    fogMemory.clear();
    if (fogReceived) ingestFog();
    applyFogAll();
}

function degradeSidc(sidc) {
    // Keep scheme + affiliation + dimension + status; blank the function ID and
    // modifiers so milsymbol draws just the affiliation frame — the 2525C way
    // to say "contact here, this side, type unknown."
    if (typeof sidc !== "string" || sidc.length < 4) return sidc;
    return sidc.slice(0, 4) + "-----------"; // 4 + 11 = 15
}

function buildGhostIcon(sidc) {
    // Last-known position: monochrome grey so it reads as stale memory, not a
    // live contact. The age fade is applied to the marker element (setOpacity),
    // not baked into the symbol.
    const symbol = new ms.Symbol(sidc, { size: SYMBOL_SIZE, monoColor: FOG_GHOST_COLOR });
    const anchor = symbol.getAnchor();
    return L.divIcon({
        className: "milsymbol fog-ghost",
        html: symbol.asSVG(),
        iconSize: [symbol.getSize().width, symbol.getSize().height],
        iconAnchor: [anchor.x, anchor.y],
    });
}

function buildFogIcon(sidc, mode, selected) {
    if (mode === "type-unknown") return buildSymbolIcon(degradeSidc(sidc), selected);
    if (mode === "ghost") return buildGhostIcon(sidc);
    if (mode === "ghost-unknown") return buildGhostIcon(degradeSidc(sidc));
    return buildSymbolIcon(sidc, selected);
}

function fogIconMode(u) {
    if (!fogActive() || u.coalition === activeViewpointCoalition()) return "real";
    const info = fogVisInfo(u);
    if (!info.show) return "real"; // hidden anyway — cheap default
    if (info.ghost) return info.typeKnown ? "ghost" : "ghost-unknown";
    if (!info.typeKnown) return "type-unknown";
    return "real";
}

// Single funnel for all unit-icon changes (fog mode, sidc change, selection).
// Tracks the last-applied key so we only rebuild the SVG when something
// actually changed — icon rebuilds aren't free at scale.
function refreshUnitIcon(entry) {
    const u = entry.data;
    const selected = u.id === selectedUnitId;
    const mode = fogIconMode(u);
    const key = `${mode}|${u.sidc}|${selected ? 1 : 0}`;
    if (entry.fogIconKey === key) return;
    entry.fogIconKey = key;
    entry.marker.setIcon(buildFogIcon(u.sidc, mode, selected));
}

function applyFogRing(entry, want) {
    const u = entry.data;
    if (want) {
        if (!entry.fogRing) {
            entry.fogRing = L.circle([u.lat, u.lon], {
                radius: FOG_RING_RADIUS_M,
                color: FOG_RING_COLOR,
                weight: 1.5,
                opacity: 0.9,
                dashArray: "4 4",
                fill: false,
                interactive: false,
            });
        } else {
            entry.fogRing.setLatLng([u.lat, u.lon]);
        }
        if (!entry.fogRingVisible) {
            entry.fogRing.addTo(map);
            entry.fogRingVisible = true;
        }
    } else if (entry.fogRing && entry.fogRingVisible) {
        entry.fogRing.remove();
        entry.fogRingVisible = false;
    }
}

function teardownFogRing(entry) {
    if (!entry.fogRing) return;
    if (entry.fogRingVisible) entry.fogRing.remove();
    entry.fogRing = null;
    entry.fogRingVisible = false;
}

// Apply fog rendering to one unit: icon mode, element opacity (ghost fade), and
// the range-unknown uncertainty ring. Assumes visibility was already applied.
function applyFogStyle(entry) {
    const u = entry.data;
    const info = fogVisInfo(u);
    refreshUnitIcon(entry);
    const opacity = info.show ? info.opacity : 1;
    if (entry.fogOpacity !== opacity) {
        entry.marker.setOpacity(opacity);
        entry.fogOpacity = opacity;
    }
    const wantRing =
        fogActive() &&
        info.show &&
        info.live &&
        info.distanceUnknown &&
        u.coalition !== activeViewpointCoalition();
    applyFogRing(entry, wantRing);
}

function applyFogAll() {
    for (const entry of unitsById.values()) {
        applyVisibility(entry);
        applyFogStyle(entry);
        applyThreatVisibility(entry);
        applyVectorVisibility(entry);
        applyTrailVisibility(entry);
    }
    updateFogHint();
}

function updateFogHint() {
    const hint = document.getElementById("fogHint");
    if (hint) hint.hidden = !(FILTERS.fog.on && !fogEvalOk);
}

function applyFogSnapshot(msg) {
    fogContacts = msg.by_coalition || {};
    fogEvalOk = msg.eval_ok !== false;
    fogReceived = true;
    if (FILTERS.fog.on) {
        ingestFog();
        applyFogAll();
    } else {
        updateFogHint();
    }
}

function syncFogControls() {
    const t = document.getElementById("fogToggle");
    const vp = document.getElementById("fogViewpointSel");
    const mem = document.getElementById("fogMemorySel");
    if (t) t.checked = FILTERS.fog.on;
    if (vp) vp.value = FILTERS.fog.viewpoint;
    if (mem) mem.value = String(FILTERS.fog.memorySec);
    const off = !FILTERS.fog.on;
    if (vp) vp.disabled = off;
    if (mem) mem.disabled = off;
    const vpRow = document.getElementById("fogViewpointRow");
    if (vpRow) vpRow.classList.toggle("filter-row-disabled", off);
    const memRow = document.getElementById("fogMemoryRow");
    if (memRow) memRow.classList.toggle("filter-row-disabled", off);
    updateFogHint();
}

function wireFogControls() {
    const t = document.getElementById("fogToggle");
    const vp = document.getElementById("fogViewpointSel");
    const mem = document.getElementById("fogMemorySel");
    if (t) {
        t.addEventListener("change", () => {
            FILTERS.fog.on = t.checked;
            encodeHash();
            syncFogControls();
            resetFogViewpoint();
        });
    }
    if (vp) {
        vp.addEventListener("change", () => {
            FILTERS.fog.viewpoint = vp.value;
            encodeHash();
            resetFogViewpoint();
        });
    }
    if (mem) {
        mem.addEventListener("change", () => {
            const n = parseInt(mem.value, 10);
            if (!FOG_MEMORY_CHOICES.includes(n)) return;
            FILTERS.fog.memorySec = n;
            encodeHash();
            applyFogAll();
        });
    }
}

function encodeView() {
    if (!map) return null;
    const c = map.getCenter();
    // 4 decimal degrees ≈ 11 m at the equator — plenty for view restoration.
    return `${c.lat.toFixed(4)},${c.lng.toFixed(4)},${map.getZoom()}`;
}

function encodeHash() {
    const c = Object.entries(FILTERS.coalition)
        .filter(([, on]) => on)
        .map(([k]) => HASH_COAL[k])
        .join("");
    const g = Object.entries(FILTERS.category)
        .filter(([, on]) => on)
        .map(([k]) => HASH_CAT[k])
        .join("");
    const l = Object.entries(FILTERS.layers)
        .filter(([, on]) => on)
        .map(([k]) => HASH_LAYER[k])
        .join("");
    const filtersAllOn = c.length === 3 && g.length === N_CAT_FLAGS && l.length === N_LAYER_FLAGS;
    const view = encodeView();
    const parts = [];
    if (!filtersAllOn) parts.push(`coal=${c}`, `cat=${g}`, `layers=${l}`);
    if (FILTERS.trailLengthSec !== TRAIL_LENGTH_DEFAULT_SEC) {
        parts.push(`trail=${FILTERS.trailLengthSec}`);
    }
    if (FILTERS.routesMode !== ROUTES_MODE_DEFAULT) {
        parts.push(`routes=${FILTERS.routesMode}`);
    }
    if (FILTERS.fog.on) {
        parts.push(`fog=${FILTERS.fog.viewpoint}`);
        if (FILTERS.fog.memorySec !== FOG_MEMORY_DEFAULT_SEC) {
            parts.push(`fogmem=${FILTERS.fog.memorySec}`);
        }
    }
    if (activeBasemapId && activeBasemapId !== defaultBasemapId) {
        parts.push(`base=${activeBasemapId}`);
    }
    if (view) parts.push(`view=${view}`);
    const url =
        parts.length === 0
            ? window.location.pathname + window.location.search
            : `${window.location.pathname}${window.location.search}#${parts.join("&")}`;
    history.replaceState(null, "", url);
}

function decodeHash() {
    const raw = window.location.hash.replace(/^#/, "");
    if (!raw) return; // no hash → leave defaults (all on)
    const params = new URLSearchParams(raw);
    const coalCodes = params.get("coal");
    const catCodes = params.get("cat");
    const layerCodes = params.get("layers");
    if (coalCodes !== null) {
        for (const k of Object.keys(FILTERS.coalition)) FILTERS.coalition[k] = false;
        for (const ch of coalCodes) {
            const k = Object.keys(HASH_COAL).find((x) => HASH_COAL[x] === ch);
            if (k !== undefined) FILTERS.coalition[k] = true;
        }
    }
    if (catCodes !== null) {
        for (const k of Object.keys(FILTERS.category)) FILTERS.category[k] = false;
        for (const ch of catCodes) {
            const k = Object.keys(HASH_CAT).find((x) => HASH_CAT[x] === ch);
            if (k !== undefined) FILTERS.category[k] = true;
        }
    }
    if (layerCodes !== null) {
        for (const k of Object.keys(FILTERS.layers)) FILTERS.layers[k] = false;
        for (const ch of layerCodes) {
            const k = Object.keys(HASH_LAYER).find((x) => HASH_LAYER[x] === ch);
            if (k !== undefined) FILTERS.layers[k] = true;
        }
    }
    const trailStr = params.get("trail");
    if (trailStr !== null) {
        const n = parseInt(trailStr, 10);
        if (TRAIL_LENGTHS_SEC.includes(n)) {
            FILTERS.trailLengthSec = n;
            trailLengthSetByHash = true;
        }
    }
    const routesStr = params.get("routes");
    if (routesStr !== null && ROUTES_MODES.includes(routesStr)) {
        FILTERS.routesMode = routesStr;
        routesModeSetByHash = true;
    }
    const fogStr = params.get("fog");
    if (fogStr !== null) {
        FILTERS.fog.on = true;
        if (["auto", "1", "2", "3"].includes(fogStr)) FILTERS.fog.viewpoint = fogStr;
    }
    const fogMemStr = params.get("fogmem");
    if (fogMemStr !== null) {
        const n = parseInt(fogMemStr, 10);
        if (FOG_MEMORY_CHOICES.includes(n)) FILTERS.fog.memorySec = n;
    }
    const baseStr = params.get("base");
    if (baseStr !== null) pendingBasemap = baseStr; // validated against the list in setupBasemaps
    const viewStr = params.get("view");
    if (viewStr !== null) {
        const m = viewStr.match(/^(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?),(\d+(?:\.\d+)?)$/);
        if (m) {
            const lat = parseFloat(m[1]);
            const lon = parseFloat(m[2]);
            const zoom = parseFloat(m[3]);
            if (
                Number.isFinite(lat) && lat >= -90 && lat <= 90 &&
                Number.isFinite(lon) && lon >= -180 && lon <= 180 &&
                Number.isFinite(zoom) && zoom >= 0 && zoom <= 22
            ) {
                pendingView = { center: [lat, lon], zoom };
            }
        }
    }
}

function readTrailLengthFromStorage() {
    try {
        const v = parseInt(localStorage.getItem(TRAIL_LS_KEY), 10);
        if (TRAIL_LENGTHS_SEC.includes(v)) return v;
    } catch {
        // Private-mode browsers can throw on access. Treat as "no preference."
    }
    return null;
}

function readRoutesModeFromStorage() {
    try {
        const v = localStorage.getItem(ROUTES_MODE_LS_KEY);
        if (ROUTES_MODES.includes(v)) return v;
    } catch {
        // Private-mode browsers can throw on access. Treat as "no preference."
    }
    return null;
}

function writeRoutesModeToStorage(v) {
    try {
        localStorage.setItem(ROUTES_MODE_LS_KEY, v);
    } catch {
        // localStorage may be unavailable (private mode, quota). Best-effort.
    }
}

function writeTrailLengthToStorage(v) {
    try {
        localStorage.setItem(TRAIL_LS_KEY, String(v));
    } catch {
        // localStorage may be unavailable (private mode, quota). Best-effort.
    }
}

function syncCheckboxesFromFilters() {
    // [data-filter] scopes this to coalition/category/layer toggles — the fog
    // toggle has no data-filter and is handled by syncFogControls().
    for (const cb of document.querySelectorAll("#filters input[type=checkbox][data-filter]")) {
        const kind = cb.dataset.filter;
        const val = cb.dataset.value;
        cb.checked = FILTERS[kind][val] === true;
    }
    const sel = document.getElementById("trailLengthSel");
    if (sel) {
        sel.value = String(FILTERS.trailLengthSec);
        sel.disabled = !FILTERS.layers.trails;
    }
    const subRow = document.getElementById("trailLengthRow");
    if (subRow) subRow.classList.toggle("filter-row-disabled", !FILTERS.layers.trails);
    const routesSel = document.getElementById("routesModeSel");
    if (routesSel) {
        routesSel.value = FILTERS.routesMode;
        routesSel.disabled = !FILTERS.layers.routes;
    }
    const routesSubRow = document.getElementById("routesModeRow");
    if (routesSubRow) routesSubRow.classList.toggle("filter-row-disabled", !FILTERS.layers.routes);
}

function wireFilterCheckboxes() {
    // [data-filter] excludes the fog toggle (wired separately in wireFogControls).
    for (const cb of document.querySelectorAll("#filters input[type=checkbox][data-filter]")) {
        cb.addEventListener("change", () => {
            const kind = cb.dataset.filter;
            const val = cb.dataset.value;
            FILTERS[kind][val] = cb.checked;
            encodeHash();
            applyVisibilityAll();
            applyRouteVisibilityAll();
            applyBullseyeVisibilityAll();
            applyAirbaseVisibilityAll();
            applyRunwayVisibilityAll();
            applyNavaidVisibilityAll();
            applyMarkVisibilityAll();
            applyThreatVisibilityAll();
            applyVectorVisibilityAll();
            applyTrailVisibilityAll();
            // Clearing measure layer also clears any active measurement.
            if (kind === "layers" && val === "measure" && !cb.checked) clearMeasure();
            if (kind === "layers" && val === "trails") {
                const sel = document.getElementById("trailLengthSel");
                if (sel) sel.disabled = !cb.checked;
                const subRow = document.getElementById("trailLengthRow");
                if (subRow) subRow.classList.toggle("filter-row-disabled", !cb.checked);
            }
            if (kind === "layers" && val === "routes") {
                const sel = document.getElementById("routesModeSel");
                if (sel) sel.disabled = !cb.checked;
                const subRow = document.getElementById("routesModeRow");
                if (subRow) subRow.classList.toggle("filter-row-disabled", !cb.checked);
            }
        });
    }
    const routesModeSel = document.getElementById("routesModeSel");
    if (routesModeSel) {
        routesModeSel.addEventListener("change", () => {
            const v = routesModeSel.value;
            if (!ROUTES_MODES.includes(v)) return;
            FILTERS.routesMode = v;
            writeRoutesModeToStorage(v);
            encodeHash();
            applyRouteVisibilityAll();
        });
    }
    const trailLengthSel = document.getElementById("trailLengthSel");
    if (trailLengthSel) {
        trailLengthSel.addEventListener("change", () => {
            const n = parseInt(trailLengthSel.value, 10);
            if (!TRAIL_LENGTHS_SEC.includes(n)) return;
            FILTERS.trailLengthSec = n;
            writeTrailLengthToStorage(n);
            encodeHash();
            redrawAllTrails();
        });
    }
}

async function loadConfig() {
    const res = await fetch("/api/config");
    if (!res.ok) {
        throw new Error(`/api/config returned ${res.status}`);
    }
    return res.json();
}

function buildMap(config) {
    const m = L.map("map", {
        center: pendingView?.center ?? CAUCASUS_CENTER,
        zoom: pendingView?.zoom ?? 7,
        zoomControl: false, // +/- buttons sat under the filter panel — wheel + pinch cover zoom
        worldCopyJump: true,
    });
    // A URL-supplied view is an explicit user choice — bookmarked / shared.
    // Don't override it with auto-center on first own-ship sight; the user
    // can hit the recenter button if they want to snap to the player.
    if (pendingView) initialOwnShipCenterDone = true;

    setupBasemaps(m, config);

    m.createPane(MARKS_PANE).style.zIndex = String(MARKS_PANE_Z);
    marksRenderer = L.svg({ pane: MARKS_PANE });
    // Navaid glyphs sit on their own pane below the airbase/unit markers.
    m.createPane(NAVAIDS_PANE).style.zIndex = String(NAVAIDS_PANE_Z);

    // Persist pan/zoom into the URL hash so a refresh keeps the same view.
    m.on("moveend", encodeHash);
    // Waypoint label collisions depend on pixel distances → re-run on zoom.
    m.on("zoomend", declutterAllRouteLabels);
    // Runways fade as you zoom in (defer to the base map's own depiction).
    m.on("zoomend", applyRunwayFade);
    // Vectors are a fixed pixel length, so their lat/lon endpoints shift on zoom.
    m.on("zoomend", moveAllVectors);
    // A user drag is the explicit "I want to look elsewhere" signal that breaks
    // continuous map-follow. Wheel/double-click zoom + programmatic setView
    // intentionally do NOT break follow.
    m.on("dragstart", () => { setFollow(null); });

    recenterControl = buildRecenterControl();
    recenterControl.addTo(m);
    return m;
}

// Basemap selector. The list + default come from /api/config; the proxy serves
// every source through /tiles/<id>/… so the browser never hits upstream tile
// servers directly. One layer at a time; the choice rides the URL hash (`base=`)
// like the rest of the view state. Called once from buildMap.
function setupBasemaps(m, config) {
    basemapList = Array.isArray(config.basemaps) ? config.basemaps : [];
    defaultBasemapId = config.defaultBasemap || (basemapList[0] && basemapList[0].id) || null;
    const valid = new Set(basemapList.map((b) => b.id));
    activeBasemapId =
        pendingBasemap && valid.has(pendingBasemap) ? pendingBasemap : defaultBasemapId;

    const sel = document.getElementById("basemapSel");
    if (sel) {
        sel.innerHTML = "";
        for (const b of basemapList) {
            const opt = document.createElement("option");
            opt.value = b.id;
            opt.textContent = b.label;
            sel.appendChild(opt);
        }
        if (activeBasemapId) sel.value = activeBasemapId;
        sel.addEventListener("change", () => {
            applyBasemap(m, sel.value);
            encodeHash();
        });
    }

    if (activeBasemapId) applyBasemap(m, activeBasemapId);
}

// Swap the active basemap. Tile layers live in Leaflet's tilePane (below the
// overlay/marker panes regardless of add order), so a freshly-added base still
// renders beneath symbols. Add-then-remove avoids a no-tile flash mid-switch.
function applyBasemap(m, id) {
    const bm = basemapList.find((b) => b.id === id);
    if (!bm) return;
    const layer = L.tileLayer(bm.url, {
        maxNativeZoom: bm.maxNativeZoom,
        maxZoom: 19,
        attribution: bm.attribution,
    });
    layer.addTo(m);
    if (basemapLayer) m.removeLayer(basemapLayer);
    basemapLayer = layer;
    activeBasemapId = id;
    const sel = document.getElementById("basemapSel");
    if (sel && sel.value !== id) sel.value = id;
}

// Snap-to-player helper. Always recenters at the current zoom (so the user's
// chosen zoom is preserved across recenters), except when called from the
// initial auto-center path which passes OWN_SHIP_INITIAL_ZOOM explicitly.
function recenterOnOwnShip(zoom) {
    const u = findPlayerUnit();
    if (!u || !map) return false;
    const targetZoom = typeof zoom === "number" ? zoom : map.getZoom();
    map.setView([u.lat, u.lon], targetZoom, { animate: false });
    return true;
}

function maybeAutoCenterOnOwnShip() {
    if (initialOwnShipCenterDone) return;
    if (recenterOnOwnShip(OWN_SHIP_INITIAL_ZOOM)) {
        initialOwnShipCenterDone = true;
    }
}

// --- map follow -------------------------------------------------------------
// `followedUnitId` (declared up top) is the single source of truth. setFollow
// is the only writer, so the button's active state and the immediate recenter
// stay in lockstep with the state. The per-tick recenter (as the unit moves)
// lives in the unit_update handler.
function setFollow(id) {
    followedUnitId = id;
    updateFollowButtonState();
    if (id !== null) recenterOnUnit(id);
}

// Snap to a unit's current position at the current zoom (preserves the user's
// chosen zoom). No-op if the unit isn't on the map.
function recenterOnUnit(id) {
    const entry = unitsById.get(id);
    if (!entry || !map) return;
    map.setView([entry.data.lat, entry.data.lon], map.getZoom(), { animate: false });
}

function updateFollowButtonState() {
    if (!recenterControl) return;
    const el = recenterControl.getContainer();
    const btn = el && el.querySelector(".mizmap-recenter-btn");
    if (btn) btn.classList.toggle("is-following", followedUnitId !== null);
}

// The button is meaningful when there's something either gesture can act on:
// a selected unit (single-click follows it) or an own-ship (double-click).
function updateRecenterControlVisibility() {
    if (!recenterControl) return;
    const el = recenterControl.getContainer();
    if (!el) return;
    const usable = selectedUnitId !== null || !!findPlayerUnit();
    el.style.display = usable ? "" : "none";
}

// --- navigation mode --------------------------------------------------------

function readNavModeFromStorage() {
    try {
        return localStorage.getItem(NAV_LS_KEY) === "1";
    } catch {
        return false;
    }
}

function writeNavModeToStorage(on) {
    try {
        localStorage.setItem(NAV_LS_KEY, on ? "1" : "0");
    } catch {
        // Best-effort.
    }
}

// Find the next waypoint along the player's planned route. v1 heuristic:
// pick the closest waypoint whose direction from the player has a positive
// dot product with the player's current track vector (i.e. lies generally
// "ahead"). If no waypoint qualifies — typically the player has overflown
// the last one — return the final waypoint flagged as past.
// Returns null when no route for the player's group, otherwise
// { point, index, isPast }.
function pickNextWaypoint(player) {
    const route = routesByGroupId.get(player.group.id)?.data;
    if (!route || !route.points || route.points.length === 0) return null;
    // Equirectangular small-distance projection in degrees; the dot-product
    // sign is invariant under scale, so we don't need to convert to meters.
    const cosLat = Math.cos((player.lat * Math.PI) / 180);
    const tx = Math.sin(player.track);
    const ty = Math.cos(player.track);
    let bestIdx = -1;
    let bestDist = Infinity;
    for (let i = 0; i < route.points.length; i++) {
        const p = route.points[i];
        const dx = (p.lon - player.lon) * cosLat;
        const dy = p.lat - player.lat;
        if (dx * tx + dy * ty <= 0) continue; // behind
        // Squared planar distance is fine for ranking (haversine for the
        // final distance display is separate).
        const d2 = dx * dx + dy * dy;
        if (d2 < bestDist) {
            bestDist = d2;
            bestIdx = i;
        }
    }
    if (bestIdx === -1) {
        // All waypoints behind — overflew the route. Anchor on the last one
        // so the panel keeps showing something meaningful instead of "—".
        const lastIdx = route.points.length - 1;
        return { point: route.points[lastIdx], index: lastIdx, isPast: true };
    }
    return { point: route.points[bestIdx], index: bestIdx, isPast: false };
}

function formatNavEta(distanceM, speedMs) {
    if (!Number.isFinite(distanceM) || speedMs < NAV_ETA_MIN_SPEED_MS) return "--:--";
    const sec = Math.round(distanceM / speedMs);
    if (sec >= 60 * 60) {
        // Long-range ETAs (>1h) collapse to "Xh Ym" so the panel stays compact.
        const h = Math.floor(sec / 3600);
        const m = Math.floor((sec % 3600) / 60);
        return `${h}h ${m.toString().padStart(2, "0")}m`;
    }
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
}

const navEls = {
    panel: null, data: null, toggle: null,
    wp: null, brg: null, dist: null, eta: null,
    wpPrev: null, wpNext: null,
};

function initNavPanelRefs() {
    navEls.panel = document.getElementById("navpanel");
    navEls.data = document.getElementById("navData");
    navEls.toggle = document.getElementById("navToggle");
    navEls.wp = document.getElementById("navWp");
    navEls.brg = document.getElementById("navBrg");
    navEls.dist = document.getElementById("navDist");
    navEls.eta = document.getElementById("navEta");
    navEls.wpPrev = document.getElementById("navWpPrev");
    navEls.wpNext = document.getElementById("navWpNext");
    if (navEls.toggle) {
        navEls.toggle.addEventListener("change", () => {
            setNavMode(navEls.toggle.checked);
        });
    }
    if (navEls.wpPrev) navEls.wpPrev.addEventListener("click", () => cycleNavWp(-1));
    if (navEls.wpNext) navEls.wpNext.addEventListener("click", () => cycleNavWp(+1));
}

// Step the displayed waypoint by +1/-1 with wrap-around. Establishes a
// baseline from the auto-picked WP on the first nudge, then walks freely.
// Manual override stays in effect until nav-mode is toggled off or the
// route changes.
function cycleNavWp(delta) {
    const player = findPlayerUnit();
    if (!player) return;
    const route = routesByGroupId.get(player.group.id)?.data;
    if (!route || !route.points || route.points.length === 0) return;
    const n = route.points.length;
    let base;
    if (navWpIndexOverride !== null) {
        base = navWpIndexOverride;
    } else {
        const auto = pickNextWaypoint(player);
        base = auto ? auto.index : 0;
    }
    // ((x % n) + n) % n: positive-result modulo that wraps negatives too.
    navWpIndexOverride = ((base + delta) % n + n) % n;
    refreshNavPanel();
}

function refreshNavPanel() {
    if (!navEls.data || !navModeOn) return;
    const player = findPlayerUnit();
    if (!player) {
        navEls.wp.textContent = "—";
        navEls.brg.textContent = "—";
        navEls.dist.textContent = "—";
        navEls.eta.textContent = "—";
        return;
    }
    const route = routesByGroupId.get(player.group.id)?.data;
    if (!route || !route.points || route.points.length === 0) {
        navEls.wp.textContent = "no route";
        navEls.brg.textContent = "—";
        navEls.dist.textContent = "—";
        navEls.eta.textContent = "—";
        return;
    }
    let index, isPast;
    if (navWpIndexOverride !== null) {
        // Clamp into current route bounds — survives an out-of-bounds override
        // that lingered across a mission change (reset usually handles this,
        // but the modular form is a cheap safety net).
        const n = route.points.length;
        index = ((navWpIndexOverride % n) + n) % n;
        navWpIndexOverride = index;
        isPast = false; // user-selected: "(past)" annotation doesn't apply
    } else {
        const auto = pickNextWaypoint(player);
        index = auto.index;
        isPast = auto.isPast;
    }
    const point = route.points[index];
    const wpIdx = `WP ${index}`;
    const trimmed = point.name && point.name.trim();
    // Show both the .miz-supplied name and the numeric waypoint id so the
    // pilot can cross-reference the F10 map / kneeboard. Numeric id matches
    // the WP labels rendered on the map (0-based per route).
    const wpName = trimmed ? `${trimmed} [${wpIdx}]` : wpIdx;
    navEls.wp.textContent = isPast ? `${wpName} (past)` : wpName;
    const brgT = initialBearingDeg(player.lat, player.lon, point.lat, point.lon);
    const dec = playerDecState.value;
    const brgM = trueToMagnetic(brgT, dec);
    const suffix = dec === null ? "°T" : "°M"; // dec=null = unknown → degrade gracefully
    navEls.brg.textContent = `${String(Math.round(brgM) % 360).padStart(3, "0")}${suffix}`;
    const distNm = haversineNm(player.lat, player.lon, point.lat, point.lon);
    navEls.dist.textContent = distNm < 10
        ? `${distNm.toFixed(1)} nm`
        : `${Math.round(distNm)} nm`;
    navEls.eta.textContent = formatNavEta(distNm * 1852, player.speed || 0);
}

function setNavMode(on) {
    navModeOn = !!on;
    writeNavModeToStorage(navModeOn);
    if (navEls.data) navEls.data.hidden = !navModeOn;
    if (navEls.toggle) navEls.toggle.checked = navModeOn;
    if (navModeOn) {
        // Engage map-follow of the own-ship (if it's on the map yet).
        const player = findPlayerUnit();
        if (player) setFollow(player.id);
        refreshNavPanel();
    } else {
        setFollow(null);
        // Turning nav-mode off is also the user's "give me auto again" reset.
        navWpIndexOverride = null;
    }
}

// Single-click: toggle map-follow on the currently selected unit. No-op when
// nothing is selected (double-click is the own-ship path).
function onRecenterSingleClick() {
    if (selectedUnitId === null) return;
    setFollow(followedUnitId === selectedUnitId ? null : selectedUnitId);
}

// Double-click: select the own-ship (if present) and follow it — same outcome
// regardless of what was selected or followed before. No-op without an own-ship.
function onRecenterDoubleClick() {
    const player = findPlayerUnit();
    if (!player) return;
    selectUnit(player.id); // no-op if already selected; clears any prior follow
    setFollow(player.id);
}

function buildRecenterControl() {
    const Ctrl = L.Control.extend({
        options: { position: "bottomleft" },
        onAdd() {
            const container = L.DomUtil.create(
                "div",
                "leaflet-bar leaflet-control mizmap-recenter",
            );
            const btn = L.DomUtil.create("a", "mizmap-recenter-btn", container);
            btn.href = "#";
            btn.title = "Follow selected unit — double-click to follow own-ship";
            btn.setAttribute("role", "button");
            btn.setAttribute(
                "aria-label",
                "Follow selected unit; double-click to follow own-ship",
            );
            // Inline SVG: crosshair (concentric circle + four ticks). Matches
            // the existing minimal-line aesthetic of the other map glyphs
            // (bullseye, ruler endpoint).
            btn.innerHTML = `
<svg viewBox="0 0 22 22" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
  <circle cx="11" cy="11" r="6" />
  <circle cx="11" cy="11" r="1.5" fill="currentColor" stroke="none" />
  <line x1="11" y1="1" x2="11" y2="4" />
  <line x1="11" y1="18" x2="11" y2="21" />
  <line x1="1" y1="11" x2="4" y2="11" />
  <line x1="18" y1="11" x2="21" y2="11" />
</svg>`.trim();
            // Keep map drag/zoom (incl. dblclick-zoom) from firing under the btn.
            L.DomEvent.disableClickPropagation(container);
            // A Leaflet control can't natively tell single from double click, so
            // debounce: a lone click fires its action after the dblclick window;
            // a second click within it cancels the pending single and fires the
            // double instead.
            let clickTimer = null;
            L.DomEvent.on(btn, "click", (ev) => {
                L.DomEvent.stop(ev);
                if (clickTimer !== null) return; // 2nd click → dblclick handles it
                clickTimer = setTimeout(() => {
                    clickTimer = null;
                    onRecenterSingleClick();
                }, RECENTER_DBLCLICK_MS);
            });
            L.DomEvent.on(btn, "dblclick", (ev) => {
                L.DomEvent.stop(ev);
                if (clickTimer !== null) {
                    clearTimeout(clickTimer);
                    clickTimer = null;
                }
                onRecenterDoubleClick();
            });
            // Hidden until a player unit appears or a unit is selected.
            container.style.display = "none";
            return container;
        },
    });
    return new Ctrl();
}

// wsStatus/grpcStatus are colored dots (no text) in the panel top bar; state
// shows as the dot color + a hover tooltip naming the link. The tooltip is the
// app-styled .conn-dot::after, which reads aria-label (also the a11y name).
function setStatus(el, ok, name) {
    el.classList.toggle("status-up", ok);
    el.classList.toggle("status-down", !ok);
    el.setAttribute("aria-label", `${name}: ${ok ? "connected" : "disconnected"}`);
}

function applyGrpcStatus(msg) {
    setStatus(grpcStatusEl, !!msg.connected, "DCS-gRPC");
    if (msg.connected || !msg.error) {
        grpcErrorEl.hidden = true;
        grpcErrorEl.textContent = "";
    } else {
        grpcErrorEl.hidden = false;
        grpcErrorEl.textContent = msg.error;
    }
}

// --- telemetry HUD -----------------------------------------------------------

function findPlayerUnit() {
    for (const { data } of unitsById.values()) {
        if (data.player_name) return data;
    }
    return null;
}

// HUD source-of-truth: the explicitly-selected unit wins; otherwise fall
// back to the player's own ship. If the selected id has gone stale (filtered
// out, unit gone, snapshot replaced), the caller's responsible for clearing
// it — we just degrade to own-ship here without mutating state.
function getHudUnit() {
    if (selectedUnitId !== null) {
        const sel = unitsById.get(selectedUnitId);
        if (sel) return sel.data;
    }
    return findPlayerUnit();
}

function formatLat(lat) {
    const hemi = lat >= 0 ? "N" : "S";
    return `${Math.abs(lat).toFixed(4)}°${hemi}`;
}
function formatLon(lon) {
    const hemi = lon >= 0 ? "E" : "W";
    return `${Math.abs(lon).toFixed(4)}°${hemi}`;
}
function formatMgrs(lat, lon) {
    try {
        // mgrs library expects [lon, lat] order — easy gotcha
        const raw = mgrs.forward([lon, lat], MGRS_ACCURACY);
        // Pretty: "37TDM63214523" → "37T DM 6321 4523"
        const m = raw.match(/^(\d{1,2}[A-Z])([A-Z]{2})(\d+)$/);
        if (!m) return raw;
        const digits = m[3];
        const half = digits.length / 2;
        return `${m[1]} ${m[2]} ${digits.slice(0, half)} ${digits.slice(half)}`;
    } catch {
        return "—";
    }
}

// Degrees-decimal-minutes — the format pilots enter into the jet (vs the HUD's
// plain decimal degrees). `degPad` zero-pads the degree field (2 for lat, 3 for
// lon) for tabular alignment. The carry guard handles minutes rounding up to
// 60.000 (e.g. 59.9997') so it rolls into the next degree rather than printing
// "60.000'".
function formatDdmPart(coord, posHemi, negHemi, degPad) {
    const hemi = coord >= 0 ? posHemi : negHemi;
    const abs = Math.abs(coord);
    let deg = Math.floor(abs);
    let min = (abs - deg) * 60;
    if (Math.round(min * 1000) >= 60000) {
        deg += 1;
        min = 0;
    }
    const degStr = String(deg).padStart(degPad, "0");
    const minStr = min.toFixed(3).padStart(6, "0");
    return `${hemi}${degStr}°${minStr}'`;
}

function formatLatLonDdm(lat, lon) {
    return `${formatDdmPart(lat, "N", "S", 2)} ${formatDdmPart(lon, "E", "W", 3)}`;
}

function refreshTelemetry() {
    const u = getHudUnit();
    const isSelected = selectedUnitId !== null && u && u.id === selectedUnitId;
    if (tlmEls.name) {
        tlmEls.name.textContent = u ? (u.callsign || u.name || "—") : "—";
        tlmEls.name.classList.toggle("tlm-name-selected", isSelected);
    }
    telemetryEl.dataset.selected = isSelected ? "true" : "false";
    if (!u) {
        telemetryEl.dataset.empty = "true";
        for (const k of Object.keys(tlmEls)) {
            if (k === "name") continue;
            tlmEls[k].textContent = "—";
        }
        return;
    }
    telemetryEl.dataset.empty = "false";
    tlmEls.lat.textContent = formatLat(u.lat);
    tlmEls.lon.textContent = formatLon(u.lon);
    tlmEls.mgrs.textContent = formatMgrs(u.lat, u.lon);
    tlmEls.alt.textContent = `${Math.round(u.alt * M_TO_FT)} ft`;
    tlmEls.gs.textContent = `${Math.round(u.speed * M_PER_S_TO_KTS)} kts`;
    const vsFpm = Math.round((u.vs || 0) * M_PER_S_TO_FT_PER_MIN);
    // Always show sign so climb/descent reads at a glance even for tiny values.
    const vsStr = vsFpm >= 0 ? `+${vsFpm}` : `${vsFpm}`;
    tlmEls.vs.textContent = `${vsStr} fpm`;
    const hdgT = (u.heading * 180) / Math.PI;
    const dec = playerDecState.value;
    const hdgDisplay = trueToMagnetic(hdgT, dec);
    const suffix = dec === null ? "°T" : "°M";
    tlmEls.hdg.textContent = `${String(Math.round(hdgDisplay) % 360).padStart(3, "0")}${suffix}`;
    // Periodically refresh the player's declination — fire-and-forget; will
    // call back into refreshTelemetry once it resolves.
    maybeRefreshPlayerDeclination(u.lat, u.lon);
}

function applyVisibility(entry) {
    const show = shouldShow(entry.data);
    if (show && !entry.visible) {
        entry.marker.addTo(map);
        entry.visible = true;
    } else if (!show && entry.visible) {
        entry.marker.remove();
        entry.visible = false;
    }
}

function applyVisibilityAll() {
    for (const entry of unitsById.values()) applyVisibility(entry);
}

// Selected units render with a white interior fill — matches DCS F10's
// convention for "selected." Frame color (affiliation outline) is preserved
// so the unit is still readable. Applied per-affiliation via milsymbol's
// `colorMode` override.
const SELECTED_FILL_MODE = {
    Friend: "#ffffff",
    Hostile: "#ffffff",
    Neutral: "#ffffff",
    Unknown: "#ffffff",
    Civilian: "#ffffff",
};

function buildSymbolIcon(sidc, selected = false) {
    const opts = { size: SYMBOL_SIZE };
    if (selected) opts.colorMode = SELECTED_FILL_MODE;
    const symbol = new ms.Symbol(sidc, opts);
    const anchor = symbol.getAnchor();
    return L.divIcon({
        className: "milsymbol",
        html: symbol.asSVG(),
        iconSize: [symbol.getSize().width, symbol.getSize().height],
        iconAnchor: [anchor.x, anchor.y],
    });
}

function tooltipFor(u) {
    const altFt = Math.round(u.alt * M_TO_FT).toLocaleString("en-US");
    const spdKts = Math.round(u.speed * M_PER_S_TO_KTS);
    return `<b>${u.callsign || u.name}</b><br>${u.type || ""}<br>alt ${altFt} ft · spd ${spdKts} kts`;
}

function upsertUnit(u) {
    const existing = unitsById.get(u.id);
    if (existing) {
        existing.marker.setLatLng([u.lat, u.lon]);
        existing.marker.setTooltipContent(tooltipFor(u));
        const prevThreat = existing.data.threat_km;
        existing.data = u;
        applyVisibility(existing);
        // Fog rendering (icon mode / opacity / uncertainty ring) tracks the
        // fresh data; refreshUnitIcon inside also rebuilds the icon on a SIDC
        // change (affiliation/category shift), preserving selection state.
        applyFogStyle(existing);
        // Threat ring: rebuild on threat_km change (rare — type-bound), else
        // just move it. Move first, then re-evaluate visibility.
        if (prevThreat !== u.threat_km) {
            teardownThreatRing(existing);
            buildThreatRing(existing);
        } else {
            moveThreatRing(existing, u.lat, u.lon);
        }
        applyThreatVisibility(existing);
        // Movement vector tracks position/heading/speed every tick.
        moveVector(existing);
        applyVectorVisibility(existing);
        // Trail buffer grows by one point each tick.
        recordTrailPosition(existing, u.lat, u.lon);
        moveTrail(existing);
        applyTrailVisibility(existing);
        return;
    }
    const marker = L.marker([u.lat, u.lon], {
        icon: buildSymbolIcon(u.sidc),
        keyboard: false,
        interactive: true,
    });
    marker.bindTooltip(tooltipFor(u), { direction: "top", offset: [0, -10] });
    // Left-click on the unit selects it (white highlight + HUD shows its
    // telemetry instead of own-ship + sticky tooltip). Click again to
    // deselect. Click a different unit to swap selection. Measurement uses
    // middle-click on desktop / the kneeboard MEASURE button on touch.
    marker.on("click", () => handleUnitClick(u.id));
    const entry = {
        marker,
        data: u,
        visible: false,
        threatGroup: null,
        threatCircles: null,
        threatVisible: false,
        vectorGroup: null,
        vectorLines: null,
        vectorVisible: false,
        trailPositions: null,
        trailGroup: null,
        trailSegments: null,
        trailVisible: false,
        // Fog: icon-key starts at the real (unselected) icon we just built, so
        // refreshUnitIcon is a no-op unless the lens degrades this unit.
        fogIconKey: `real|${u.sidc}|0`,
        fogOpacity: 1,
        fogRing: null,
        fogRingVisible: false,
    };
    unitsById.set(u.id, entry);
    applyVisibility(entry);
    applyFogStyle(entry);
    buildThreatRing(entry);
    applyThreatVisibility(entry);
    applyVectorVisibility(entry);
    // Seed the trail with the first known position; trail won't show until
    // a second position arrives next tick (shouldShowTrail requires >= 2).
    recordTrailPosition(entry, u.lat, u.lon);
    applyTrailVisibility(entry);
}

function removeUnit(id) {
    const entry = unitsById.get(id);
    if (entry) {
        if (entry.visible) entry.marker.remove();
        teardownThreatRing(entry);
        teardownVector(entry);
        teardownTrail(entry);
        teardownFogRing(entry);
        unitsById.delete(id);
    }
    fogMemory.delete(id);
    if (followedUnitId === id) setFollow(null);
    if (selectedUnitId === id) {
        selectedUnitId = null;
        refreshTelemetry();
        // The selection pinned its group's route in focus mode; unpin. (The
        // own-ship case is covered by the player-fingerprint hook callers
        // run after removeUnit.)
        if (FILTERS.routesMode === "focus") applyRouteVisibilityAll();
    }
}

// --- threat rings -----------------------------------------------------------

function buildThreatRing(entry) {
    const u = entry.data;
    if (typeof u.threat_km !== "number" || u.threat_km <= 0) return;
    const color = COALITION_COLOR[u.coalition] || COALITION_COLOR[1];
    const latlng = [u.lat, u.lon];
    const radiusM = u.threat_km * 1000;
    const group = L.layerGroup();
    // Cased pair: casing first (wider, solid black), then dashed colored overlay.
    const casing = L.circle(latlng, {
        radius: radiusM,
        color: CASING_COLOR,
        weight: 5,
        opacity: CASING_OPACITY,
        fill: false,
        interactive: false,
    }).addTo(group);
    const overlay = L.circle(latlng, {
        radius: radiusM,
        color,
        weight: 2,
        opacity: 0.9,
        dashArray: "8 6",
        fill: false,
        interactive: false,
    }).addTo(group);
    entry.threatGroup = group;
    entry.threatCircles = { casing, overlay };
}

function teardownThreatRing(entry) {
    if (entry.threatGroup) {
        if (entry.threatVisible) entry.threatGroup.remove();
        entry.threatGroup = null;
        entry.threatCircles = null;
        entry.threatVisible = false;
    }
}

function moveThreatRing(entry, lat, lon) {
    if (entry.threatCircles) {
        const ll = L.latLng(lat, lon);
        entry.threatCircles.casing.setLatLng(ll);
        entry.threatCircles.overlay.setLatLng(ll);
    }
}

function applyThreatVisibility(entry) {
    if (!entry.threatGroup) return;
    const show = shouldShowThreat(entry.data);
    if (show && !entry.threatVisible) {
        entry.threatGroup.addTo(map);
        entry.threatVisible = true;
    } else if (!show && entry.threatVisible) {
        entry.threatGroup.remove();
        entry.threatVisible = false;
    }
}

function applyThreatVisibilityAll() {
    for (const entry of unitsById.values()) applyThreatVisibility(entry);
}

// --- movement vectors -------------------------------------------------------

// Haversine destination — correct anywhere on the globe, six lines of JS. At
// theater latitudes a flat-earth approximation would also work, but no reason
// to be wrong-by-default.
function projectLatLon(lat, lon, bearingRad, distanceM) {
    const δ = distanceM / EARTH_RADIUS_M;
    const φ1 = (lat * Math.PI) / 180;
    const λ1 = (lon * Math.PI) / 180;
    const sinφ2 =
        Math.sin(φ1) * Math.cos(δ) + Math.cos(φ1) * Math.sin(δ) * Math.cos(bearingRad);
    const φ2 = Math.asin(sinφ2);
    const λ2 =
        λ1 +
        Math.atan2(
            Math.sin(bearingRad) * Math.sin(δ) * Math.cos(φ1),
            Math.cos(δ) - Math.sin(φ1) * sinφ2,
        );
    return [(φ2 * 180) / Math.PI, (λ2 * 180) / Math.PI];
}

function shouldShowVector(entry) {
    if (!entry.visible) return false;
    if (FILTERS.layers.vectors !== true) return false;
    // No live velocity knowledge for a ghost/undetected contact under fog.
    if (!fogVisInfo(entry.data).live) return false;
    const speed = entry.data.speed;
    return typeof speed === "number" && speed >= VECTOR_MIN_SPEED_MS;
}

function vectorLatLngs(u) {
    // Use `track` (direction of motion) not `heading` (nose direction). They
    // diverge for aircraft in crosswind, skidding vehicles, or stationary
    // units with jittery nose physics.
    // Fixed pixel length: offset the endpoint in screen space (bearing 0 = north
    // = up = −y), then unproject. Stays VECTOR_LENGTH_PX long at any zoom/speed.
    const start = map.latLngToContainerPoint([u.lat, u.lon]);
    const end = map.containerPointToLatLng([
        start.x + Math.sin(u.track) * VECTOR_LENGTH_PX,
        start.y - Math.cos(u.track) * VECTOR_LENGTH_PX,
    ]);
    return [[u.lat, u.lon], end];
}

function buildVector(entry) {
    const u = entry.data;
    const color = COALITION_COLOR[u.coalition] || COALITION_COLOR[1];
    const latlngs = vectorLatLngs(u);
    const group = L.layerGroup();
    const casing = L.polyline(latlngs, {
        color: CASING_COLOR,
        weight: VECTOR_WEIGHT + 2,
        opacity: CASING_OPACITY,
        interactive: false,
    }).addTo(group);
    const overlay = L.polyline(latlngs, {
        color,
        weight: VECTOR_WEIGHT,
        opacity: 0.85,
        interactive: false,
    }).addTo(group);
    entry.vectorGroup = group;
    entry.vectorLines = { casing, overlay };
}

function teardownVector(entry) {
    if (!entry.vectorGroup) return;
    if (entry.vectorVisible) entry.vectorGroup.remove();
    entry.vectorGroup = null;
    entry.vectorLines = null;
    entry.vectorVisible = false;
}

function moveVector(entry) {
    if (!entry.vectorLines) return;
    const latlngs = vectorLatLngs(entry.data);
    entry.vectorLines.casing.setLatLngs(latlngs);
    entry.vectorLines.overlay.setLatLngs(latlngs);
}

function applyVectorVisibility(entry) {
    const want = shouldShowVector(entry);
    if (want && !entry.vectorGroup) buildVector(entry);
    if (want && !entry.vectorVisible) {
        entry.vectorGroup.addTo(map);
        entry.vectorVisible = true;
    } else if (!want && entry.vectorVisible) {
        entry.vectorGroup.remove();
        entry.vectorVisible = false;
    }
}

function applyVectorVisibilityAll() {
    for (const entry of unitsById.values()) applyVectorVisibility(entry);
}

function moveAllVectors() {
    for (const entry of unitsById.values()) {
        if (entry.vectorVisible) moveVector(entry);
    }
}

// --- trails -----------------------------------------------------------------

function recordTrailPosition(entry, lat, lon) {
    if (!entry.trailPositions) entry.trailPositions = [];
    entry.trailPositions.push([lat, lon]);
    if (entry.trailPositions.length > TRAIL_BUFFER_MAX) entry.trailPositions.shift();
}

function shouldShowTrail(entry) {
    if (!entry.visible) return false;
    if (FILTERS.layers.trails !== true) return false;
    // A ghost/undetected contact shouldn't trail its live path under fog.
    if (!fogVisInfo(entry.data).live) return false;
    return (entry.trailPositions?.length ?? 0) >= 2;
}

function buildTrail(entry) {
    const color = COALITION_COLOR[entry.data.coalition] || COALITION_COLOR[1];
    const group = L.layerGroup();
    const segments = [];
    for (let i = 0; i < TRAIL_SEGMENTS; i++) {
        // i=0 oldest, i=last newest
        const t = i / (TRAIL_SEGMENTS - 1);
        const opacity =
            TRAIL_OPACITY_OLDEST + t * (TRAIL_OPACITY_NEWEST - TRAIL_OPACITY_OLDEST);
        const poly = L.polyline([], {
            color,
            weight: TRAIL_WEIGHT,
            opacity,
            interactive: false,
        }).addTo(group);
        segments.push(poly);
    }
    entry.trailGroup = group;
    entry.trailSegments = segments;
}

function moveTrail(entry) {
    if (!entry.trailSegments) return;
    const buf = entry.trailPositions ?? [];
    // Display only the last FILTERS.trailLengthSec tail of the buffer. Lets the
    // user lengthen the trail and immediately see existing history without
    // waiting for the buffer to fill.
    const pts = buf.length > FILTERS.trailLengthSec
        ? buf.slice(buf.length - FILTERS.trailLengthSec)
        : buf;
    if (pts.length < 2) {
        for (const seg of entry.trailSegments) seg.setLatLngs([]);
        return;
    }
    // Partition pts into TRAIL_SEGMENTS contiguous slices, with each slice
    // overlapping its neighbour by 1 point so the gradient has no visual gaps.
    const n = pts.length;
    for (let i = 0; i < TRAIL_SEGMENTS; i++) {
        const start = Math.floor((i * (n - 1)) / TRAIL_SEGMENTS);
        const end = Math.floor(((i + 1) * (n - 1)) / TRAIL_SEGMENTS) + 1;
        entry.trailSegments[i].setLatLngs(pts.slice(start, end));
    }
}

function redrawAllTrails() {
    for (const entry of unitsById.values()) {
        if (entry.trailSegments) moveTrail(entry);
    }
}

function teardownTrail(entry) {
    if (!entry.trailGroup) return;
    if (entry.trailVisible) entry.trailGroup.remove();
    entry.trailGroup = null;
    entry.trailSegments = null;
    entry.trailVisible = false;
}

function applyTrailVisibility(entry) {
    const want = shouldShowTrail(entry);
    if (want && !entry.trailGroup) {
        buildTrail(entry);
        moveTrail(entry);
    }
    if (want && !entry.trailVisible) {
        entry.trailGroup.addTo(map);
        entry.trailVisible = true;
    } else if (!want && entry.trailVisible) {
        entry.trailGroup.remove();
        entry.trailVisible = false;
    }
}

function applyTrailVisibilityAll() {
    for (const entry of unitsById.values()) applyTrailVisibility(entry);
}

function applySnapshot(units) {
    // Drop everything currently rendered, repopulate from the snapshot.
    for (const entry of unitsById.values()) {
        if (entry.visible) entry.marker.remove();
        teardownThreatRing(entry);
        teardownVector(entry);
        teardownTrail(entry);
        teardownFogRing(entry);
    }
    unitsById.clear();
    // A snapshot replace can be a mission change — the old viewpoint's
    // detection memory no longer maps to live units.
    fogMemory.clear();
    // A snapshot replace can be a mission change; the previously-selected
    // id may no longer correspond to a real unit. Clear selection; the next
    // refreshTelemetry (from incoming unit_updates) will fall back to own
    // ship cleanly.
    if (selectedUnitId !== null) {
        selectedUnitId = null;
        refreshTelemetry();
    }
    // A mission/snapshot reset stops any active follow (the followed id may no
    // longer map to a real unit). Unconditional — also covers nav-following the
    // own-ship with nothing selected.
    setFollow(null);
    for (const u of units) upsertUnit(u);
    refreshVisibilityIfPlayerChanged();
    // The fingerprint hook above only fires on a player change, but the
    // forced deselect needs focus-mode routes re-evaluated regardless. Must
    // run after the upserts so shouldShowRoute sees the new player/units.
    if (FILTERS.routesMode === "focus") applyRouteVisibilityAll();
    maybeAutoCenterOnOwnShip();
    updateRecenterControlVisibility();
}

// --- routes / waypoints -----------------------------------------------------

function tooltipForWaypoint(point, index) {
    const eta = Math.round(point.eta);
    const min = Math.floor(eta / 60);
    const sec = (eta % 60).toString().padStart(2, "0");
    const altFt = Math.round(point.alt * M_TO_FT).toLocaleString("en-US");
    const spdKts = Math.round(point.speed * M_PER_S_TO_KTS);
    return `<b>WP ${index}</b><br>${point.type || ""}${point.action ? " · " + point.action : ""}<br>alt ${altFt} ft · spd ${spdKts} kts · ETA ${min}:${sec}`;
}

// Render `latlngs` as a "cased" polyline: a solid dark underlay (always
// non-dashed so dashed overlays read as bright stripes against it) + the
// caller-styled colored overlay on top. `extra` of 3 = ~1.5px of dark border
// on each side of the colored line.
function addCasedPolyline(group, latlngs, overlayOpts, extra = 3) {
    L.polyline(latlngs, {
        color: CASING_COLOR,
        weight: (overlayOpts.weight ?? 2) + extra,
        opacity: CASING_OPACITY,
        interactive: false,
    }).addTo(group);
    L.polyline(latlngs, { interactive: false, ...overlayOpts }).addTo(group);
}

function buildRouteLayer(route) {
    const color = COALITION_COLOR[route.coalition] || COALITION_COLOR[1];
    const latlngs = route.points.map((p) => [p.lat, p.lon]);
    const group = L.layerGroup();
    if (latlngs.length >= 2) {
        addCasedPolyline(group, latlngs, {
            color,
            weight: ROUTE_WEIGHT,
            opacity: 0.95,
            dashArray: "4 4",
        });
    }
    const wpLabels = [];
    route.points.forEach((p, i) => {
        // Waypoint dot: dark halo (slightly larger, no fill stroke difference)
        // sat under the colored ring → same casing idea as the polylines.
        L.circleMarker([p.lat, p.lon], {
            radius: WAYPOINT_RADIUS + 1.5,
            color: CASING_COLOR,
            weight: 3,
            opacity: CASING_OPACITY,
            fill: false,
            interactive: false,
        }).addTo(group);
        L.circleMarker([p.lat, p.lon], {
            radius: WAYPOINT_RADIUS,
            color,
            weight: 1.5,
            fillColor: "#0b0b0b",
            fillOpacity: 0.95,
        })
            .bindTooltip(tooltipForWaypoint(p, i), { direction: "top", offset: [0, -6] })
            .addTo(group);
        // Permanent label — name from the .miz if non-empty, else "WP N".
        // Standalone L.tooltip so the circleMarker's hover-detail tooltip
        // survives. Coloured per coalition via the CSS class suffix.
        const labelText = (p.name && p.name.trim()) || `WP ${i}`;
        const label = L.tooltip({
            permanent: true,
            direction: "right",
            offset: [6, 0],
            className: `waypoint-label waypoint-label-coal${route.coalition}`,
            opacity: 1,
            interactive: false,
        })
            .setLatLng([p.lat, p.lon])
            .setContent(labelText)
            .addTo(group);
        wpLabels.push(label);
    });
    // Stashed for declutterRouteLabels, which runs on route show + zoomend.
    group._wpLabels = wpLabels;
    return group;
}

function applyRouteVisibility(entry) {
    const show = shouldShowRoute(entry.data);
    if (show && !entry.visible) {
        entry.layer.addTo(map);
        entry.visible = true;
        // Labels need to be on the map (so `_container` exists) before
        // declutter can read their pixel positions.
        declutterRouteLabels(entry.layer._wpLabels);
    } else if (!show && entry.visible) {
        entry.layer.remove();
        entry.visible = false;
    }
}

function applyRouteVisibilityAll() {
    for (const entry of routesByGroupId.values()) applyRouteVisibility(entry);
}

// Pixel-distance declutter for waypoint labels within a single route. Walks
// labels in route order; hides any label that lands within
// WP_LABEL_MIN_PIXELS of one already kept. Run on route show and on every
// zoomend, since pixel distances change with zoom.
const WP_LABEL_MIN_PIXELS = 22;
const WP_LABEL_HIDDEN_CLASS = "waypoint-label-hidden";

function declutterRouteLabels(labels) {
    if (!labels || !labels.length || !map) return;
    const placed = [];
    const minSq = WP_LABEL_MIN_PIXELS * WP_LABEL_MIN_PIXELS;
    for (const label of labels) {
        const el = label._container;
        if (!el) continue; // not yet on the map
        const px = map.latLngToContainerPoint(label.getLatLng());
        let collides = false;
        for (const q of placed) {
            const dx = q.x - px.x;
            const dy = q.y - px.y;
            if (dx * dx + dy * dy < minSq) {
                collides = true;
                break;
            }
        }
        if (collides) {
            el.classList.add(WP_LABEL_HIDDEN_CLASS);
        } else {
            el.classList.remove(WP_LABEL_HIDDEN_CLASS);
            placed.push(px);
        }
    }
}

function declutterAllRouteLabels() {
    for (const entry of routesByGroupId.values()) {
        if (entry.visible) declutterRouteLabels(entry.layer._wpLabels);
    }
}

// --- bullseyes --------------------------------------------------------------

function buildBullseyeIcon(coalition) {
    const color = COALITION_COLOR[coalition] || COALITION_COLOR[1];
    // Double-stroked for contrast: black underlay (wider) + colored overlay
    // (narrower). Same casing idea as the polylines, applied at the SVG level.
    const shapes = `
    <circle cx="16" cy="16" r="13" />
    <circle cx="16" cy="16" r="6" />
    <line x1="16" y1="1" x2="16" y2="9" />
    <line x1="16" y1="23" x2="16" y2="31" />
    <line x1="1" y1="16" x2="9" y2="16" />
    <line x1="23" y1="16" x2="31" y2="16" />`;
    const svg = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <g fill="none" stroke="${CASING_COLOR}" stroke-width="3.5" opacity="${CASING_OPACITY}">${shapes}</g>
  <g fill="none" stroke="${color}" stroke-width="1.5">${shapes}</g>
  <circle cx="16" cy="16" r="2.5" fill="${CASING_COLOR}" opacity="${CASING_OPACITY}" />
  <circle cx="16" cy="16" r="1.5" fill="${color}" />
</svg>`.trim();
    return L.divIcon({
        className: "bullseye-icon",
        html: svg,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
    });
}

const COAL_NAMES = { 1: "Neutral", 2: "Red", 3: "Blue" };

function applyBullseyeVisibility(entry) {
    const show = shouldShowBullseye(entry.data);
    if (show && !entry.visible) {
        entry.marker.addTo(map);
        entry.visible = true;
    } else if (!show && entry.visible) {
        entry.marker.remove();
        entry.visible = false;
    }
}

function applyBullseyeVisibilityAll() {
    for (const entry of bullseyesByCoalition.values()) applyBullseyeVisibility(entry);
    // Bull readout depends on bullseye availability + visibility.
    refreshMeasureReadout();
}

function applyBullseyesSnapshot(bullseyes) {
    for (const { marker, visible } of bullseyesByCoalition.values()) {
        if (visible) marker.remove();
    }
    bullseyesByCoalition.clear();
    for (const b of bullseyes) {
        const marker = L.marker([b.lat, b.lon], {
            icon: buildBullseyeIcon(b.coalition),
            interactive: true,
            keyboard: false,
        }).bindTooltip(`Bullseye (${COAL_NAMES[b.coalition] || "?"})`, {
            direction: "top",
            offset: [0, -10],
        });
        // Same click semantics as unit markers.
        marker.on("click", toggleStickyTooltip);
        const entry = { marker, data: b, visible: false };
        bullseyesByCoalition.set(b.coalition, entry);
        applyBullseyeVisibility(entry);
    }
    refreshMeasureReadout();
}

// --- airbases ---------------------------------------------------------------

function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function tooltipForAirbase(a) {
    const altFt = Math.round(a.alt * M_TO_FT).toLocaleString("en-US");
    const cat = AIRBASE_CAT_NAMES[a.category] || "Airbase";
    const coal = COAL_NAMES[a.coalition] || "?";
    const name = a.display_name || a.name || a.callsign || "Airbase";
    // Runways live here (not on the faded line, which is a poor hover target):
    // one row per runway, deduped by designator pair. Keyed on the DCS airbase
    // name, which matches each runway's airbase_name.
    const seen = new Set();
    const rwRows = [];
    for (const rw of runwaysByAirbase.get(a.name) || []) {
        const pair = runwayDesignatorPair(rw.name);
        if (seen.has(pair)) continue;
        seen.add(pair);
        rwRows.push(runwayInfoLine(rw));
    }
    const rwHtml = rwRows.length ? `<br>${rwRows.join("<br>")}` : "";
    return `<b>${escapeHtml(name)}</b><br>${cat} · ${coal}<br>elev ${altFt} ft${rwHtml}`;
}

function buildAirbaseLayer(a) {
    const group = L.layerGroup();
    const marker = L.marker([a.lat, a.lon], {
        icon: buildSymbolIcon(a.sidc),
        keyboard: false,
        interactive: true,
    });
    marker.bindTooltip(tooltipForAirbase(a), { direction: "top", offset: [0, -10] });
    // Click pins the detail tooltip (same affordance as bullseyes).
    marker.on("click", toggleStickyTooltip);
    marker.addTo(group);
    // Always-on name label to the right of the symbol — matches DCS's F10 map.
    const name = (a.display_name || a.name || a.callsign || "").trim();
    if (name) {
        L.tooltip({
            permanent: true,
            direction: "right",
            offset: [16, 0],
            className: `airbase-label airbase-label-coal${a.coalition}`,
            opacity: 1,
            interactive: false,
        })
            .setLatLng([a.lat, a.lon])
            .setContent(escapeHtml(name))
            .addTo(group);
    }
    return { group, marker };
}

// Re-render every airbase tooltip — called when the runways snapshot lands so
// fields pick up their runway rows regardless of snapshot arrival order.
function refreshAirbaseTooltips() {
    for (const entry of airbasesByName.values()) {
        if (entry.marker) entry.marker.setTooltipContent(tooltipForAirbase(entry.data));
    }
}

function applyAirbaseVisibility(entry) {
    const show = shouldShowAirbase(entry.data);
    if (show && !entry.visible) {
        entry.layer.addTo(map);
        entry.visible = true;
    } else if (!show && entry.visible) {
        entry.layer.remove();
        entry.visible = false;
    }
}

function applyAirbaseVisibilityAll() {
    for (const entry of airbasesByName.values()) applyAirbaseVisibility(entry);
}

function applyAirbasesSnapshot(airbases) {
    // Airbases are static for the mission — full replace each snapshot.
    for (const { layer, visible } of airbasesByName.values()) {
        if (visible) layer.remove();
    }
    airbasesByName.clear();
    airbases.forEach((a, i) => {
        const { group, marker } = buildAirbaseLayer(a);
        // Names are unique within a theatre; fall back to index for the rare
        // unnamed airbase so entries never collide.
        const key = (a.name && a.name.trim()) || `#${i}`;
        const entry = { layer: group, marker, data: a, visible: false };
        airbasesByName.set(key, entry);
        applyAirbaseVisibility(entry);
    });
}

// --- runways ----------------------------------------------------------------

// Pair a runway designator with its reciprocal, e.g. "06" → "06/24". DCS gives
// only one end's number; the other is 180° away (designator ±18, wrapped 1–36).
function runwayDesignatorPair(name) {
    const n = parseInt(name, 10);
    if (!Number.isFinite(n) || n < 1 || n > 36) return name || "RWY";
    const recip = ((n + 18 - 1) % 36) + 1;
    const pad = (x) => String(x).padStart(2, "0");
    return `${pad(Math.min(n, recip))}/${pad(Math.max(n, recip))}`;
}

// One runway's row for the airbase tooltip: designator pair, true heading, and
// length (ft + m). Was the runway line's own tooltip; moved to the airbase.
function runwayInfoLine(rw) {
    const hdgT = (Math.round((rw.course * 180) / Math.PI) % 360 + 360) % 360;
    const lenM = Math.round(rw.length_m);
    const lenFt = Math.round(rw.length_m * M_TO_FT).toLocaleString("en-US");
    return `RWY ${runwayDesignatorPair(rw.name)} · ${String(hdgT).padStart(3, "0")}°T · ${lenFt} ft (${lenM} m)`;
}

function buildRunwayLayer(rw) {
    const group = L.layerGroup();
    const half = rw.length_m / 2;
    const a = projectLatLon(rw.lat, rw.lon, rw.course, half);
    const b = projectLatLon(rw.lat, rw.lon, rw.course + Math.PI, half);
    // Thin halo (non-interactive) for legibility on any base-map tone — far
    // lighter than the old full casing, so it no longer reads as a runway edge.
    const casing = L.polyline([a, b], {
        color: CASING_COLOR,
        weight: RUNWAY_CASING_WEIGHT,
        opacity: RUNWAY_BASE_OPACITY * RUNWAY_CASING_RATIO,
        interactive: false,
    }).addTo(group);
    // Schematic dashed centerline — purely visual (non-interactive): its data
    // now lives in the airbase tooltip, since a faded line is a poor hover
    // target. Drawn below the airbase symbol markers (markerPane).
    const line = L.polyline([a, b], {
        color: RUNWAY_COLOR,
        weight: RUNWAY_LINE_WEIGHT,
        opacity: RUNWAY_BASE_OPACITY,
        dashArray: RUNWAY_DASH,
        interactive: false,
    });
    line.addTo(group);
    return { group, line, casing };
}

// Option 2: opacity ramps from full (zoomed out, for orientation) down to a
// faint hint (zoomed in, where the base map renders the runway itself and the
// DCS-vs-OSM tilt would otherwise clash). Linear between the two zoom bounds.
function runwayOpacityForZoom(zoom) {
    if (zoom <= RUNWAY_FADE_ZOOM_FULL) return RUNWAY_BASE_OPACITY;
    if (zoom >= RUNWAY_FADE_ZOOM_MIN) return RUNWAY_MIN_OPACITY;
    const t = (zoom - RUNWAY_FADE_ZOOM_FULL) / (RUNWAY_FADE_ZOOM_MIN - RUNWAY_FADE_ZOOM_FULL);
    return RUNWAY_BASE_OPACITY + t * (RUNWAY_MIN_OPACITY - RUNWAY_BASE_OPACITY);
}

function applyRunwayFade() {
    if (!map) return;
    const op = runwayOpacityForZoom(map.getZoom());
    for (const entry of runwaysByKey.values()) {
        if (entry.line) entry.line.setStyle({ opacity: op });
        if (entry.casing) entry.casing.setStyle({ opacity: op * RUNWAY_CASING_RATIO });
    }
}

// Runways ride the Airbases layer toggle (they're part of the airbase picture)
// and are coalition-independent — they're physical terrain, not owned by a side.
function shouldShowRunway() {
    return FILTERS.layers.airbases === true;
}

function applyRunwayVisibility(entry) {
    const show = shouldShowRunway();
    if (show && !entry.visible) {
        entry.layer.addTo(map);
        entry.visible = true;
    } else if (!show && entry.visible) {
        entry.layer.remove();
        entry.visible = false;
    }
}

function applyRunwayVisibilityAll() {
    for (const entry of runwaysByKey.values()) applyRunwayVisibility(entry);
}

function applyRunwaysSnapshot(runways) {
    // Runways are static for the mission — full replace each snapshot.
    for (const { layer, visible } of runwaysByKey.values()) {
        if (visible) layer.remove();
    }
    runwaysByKey.clear();
    runwaysByAirbase.clear();
    runways.forEach((rw, i) => {
        const { group, line, casing } = buildRunwayLayer(rw);
        const entry = { layer: group, line, casing, data: rw, visible: false };
        runwaysByKey.set(`${rw.airbase_name}/${rw.name}/${i}`, entry);
        if (!runwaysByAirbase.has(rw.airbase_name)) runwaysByAirbase.set(rw.airbase_name, []);
        runwaysByAirbase.get(rw.airbase_name).push(rw);
        applyRunwayVisibility(entry);
    });
    applyRunwayFade();
    // Runways carry the data shown in the airbase tooltip — refresh those now.
    refreshAirbaseTooltips();
}

// --- navaids ----------------------------------------------------------------

// Map a friendly navaid type to a glyph family. Chart-ish: hexagon = VOR
// family, triangle = TACAN/RSBN, square = DME, diamond = ILS/PRMG, dashed
// circle = NDB.
function navaidShape(type) {
    const t = (type || "").toUpperCase();
    if (t.startsWith("NDB")) return "ndb";
    if (t.startsWith("VOR")) return "hex"; // VOR, VOR/DME, VORTAC
    if (t.startsWith("TACAN") || t.startsWith("RSBN")) return "tri";
    if (t.startsWith("DME")) return "sq";
    if (t.startsWith("ILS") || t.startsWith("PRMG")) return "diamond";
    return "circle";
}

function navaidGlyphInner(shape) {
    // Filled silhouettes (centered in a 24×24 box). Shape alone carries type;
    // NDB is a plain disc, distinct from the polygonal aids.
    switch (shape) {
        case "hex": return '<polygon points="12,4 19,8 19,16 12,20 5,16 5,8" />';
        case "tri": return '<polygon points="12,4.5 20,19 4,19" />';
        case "sq": return '<rect x="5.5" y="5.5" width="13" height="13" />';
        case "diamond": return '<polygon points="12,3 21,12 12,21 3,12" />';
        case "ndb": return '<circle cx="12" cy="12" r="7" />';
        default: return '<circle cx="12" cy="12" r="6.5" />';
    }
}

function buildNavaidIcon(type) {
    const inner = navaidGlyphInner(navaidShape(type));
    // White halo (outline only) for separation, then the filled cyan glyph with
    // a dark edge on top — reads against reddish terrain, purple lines, and red
    // airport hatching alike.
    const svg = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${NAVAID_SIZE}" height="${NAVAID_SIZE}">
  <g fill="none" stroke="${NAVAID_HALO}" stroke-width="3.6" stroke-linejoin="round" opacity="0.95">${inner}</g>
  <g fill="${NAVAID_FILL}" stroke="${NAVAID_OUTLINE}" stroke-width="1.5" stroke-linejoin="round">${inner}</g>
</svg>`.trim();
    return L.divIcon({
        className: "navaid-icon",
        html: svg,
        iconSize: [NAVAID_SIZE, NAVAID_SIZE],
        iconAnchor: [NAVAID_SIZE / 2, NAVAID_SIZE / 2],
    });
}

function formatNavaidTune(n) {
    const parts = [];
    if (typeof n.freq_hz === "number" && n.freq_hz > 0) {
        parts.push(
            n.freq_hz >= 1e6
                ? `${(n.freq_hz / 1e6).toFixed(2)} MHz`
                : `${Math.round(n.freq_hz / 1e3)} kHz`,
        );
    }
    // TACAN/VORTAC channels carry an X/Y band, e.g. "75X".
    if (n.channel) parts.push(`Ch ${n.channel}${n.band || ""}`);
    return parts.join(" · ");
}

function tooltipForNavaid(n) {
    const cs = n.callsign ? `${escapeHtml(n.callsign)} ` : "";
    const nm = n.name ? `<br>${escapeHtml(n.name)}` : "";
    const tune = formatNavaidTune(n);
    return `<b>${cs}${escapeHtml(n.type || "Navaid")}</b>${nm}${tune ? "<br>" + tune : ""}`;
}

function shouldShowNavaid() {
    // Coalition-independent (navaids are physical infrastructure). Own toggle.
    return FILTERS.layers.navaids === true;
}

function applyNavaidVisibility(entry) {
    const show = shouldShowNavaid();
    if (show && !entry.visible) {
        entry.marker.addTo(map);
        entry.visible = true;
    } else if (!show && entry.visible) {
        entry.marker.remove();
        entry.visible = false;
    }
}

function applyNavaidVisibilityAll() {
    for (const entry of navaidsByKey.values()) applyNavaidVisibility(entry);
}

function applyNavaidsSnapshot(navaids) {
    // Static per theatre — full replace each snapshot.
    for (const { marker, visible } of navaidsByKey.values()) {
        if (visible) marker.remove();
    }
    navaidsByKey.clear();
    navaids.forEach((n, i) => {
        const marker = L.marker([n.lat, n.lon], {
            icon: buildNavaidIcon(n.type),
            pane: NAVAIDS_PANE,
            keyboard: false,
            interactive: true,
        });
        marker.bindTooltip(tooltipForNavaid(n), { direction: "top", offset: [0, -2] });
        marker.on("click", toggleStickyTooltip);
        const entry = { marker, data: n, visible: false };
        navaidsByKey.set(`${n.callsign}/${n.type}/${i}`, entry);
        applyNavaidVisibility(entry);
    });
}

// --- F10 map marks ----------------------------------------------------------

function markLabelText(m) {
    const text = m.text && m.text.trim();
    if (!text) return null;
    // HTML-escape just enough to neutralize labels containing `<` or `&`.
    // We don't render arbitrary HTML; treat the field as plain text.
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function buildMarkMarker(m) {
    const marker = L.circleMarker([m.lat, m.lon], {
        radius: MARK_RADIUS_PX,
        color: MARK_BORDER_COLOR,
        weight: MARK_BORDER_WEIGHT,
        fillColor: MARK_FILL_COLOR,
        fillOpacity: MARK_FILL_OPACITY,
        opacity: 0.95,
        interactive: true,
        pane: MARKS_PANE,
        renderer: marksRenderer,
    });
    const label = markLabelText(m);
    if (label) {
        // Always-on label, matching DCS's F10 map. Empty-text marks (player
        // marks with no caption) get no tooltip — the circle alone is enough.
        marker.bindTooltip(label, {
            direction: "top",
            offset: [0, -MARK_RADIUS_PX - 2],
            permanent: true,
            className: "mark-label",
        });
    }
    return marker;
}

function applyMarkVisibility(entry) {
    const show = shouldShowMark(entry.data);
    if (show && !entry.visible) {
        entry.marker.addTo(map);
        entry.visible = true;
    } else if (!show && entry.visible) {
        entry.marker.remove();
        entry.visible = false;
    }
}

function applyMarkVisibilityAll() {
    for (const entry of marksById.values()) applyMarkVisibility(entry);
}

// Mark visibility is keyed by the player's (coalition, group_id), and
// focus-mode route visibility by the player's group. Re-evaluate both only
// when that pair changes — calling the apply-alls on every unit_update is
// wasteful since players rarely swap coalitions or slots.
let lastPlayerVisFingerprint = "";
function refreshVisibilityIfPlayerChanged() {
    const p = findPlayerUnit();
    const fp = p ? `${p.coalition}/${p.group.id}` : "";
    if (fp === lastPlayerVisFingerprint) return;
    lastPlayerVisFingerprint = fp;
    applyMarkVisibilityAll();
    applyRouteVisibilityAll();
}

function upsertMark(m) {
    const existing = marksById.get(m.id);
    if (existing) {
        existing.marker.setLatLng([m.lat, m.lon]);
        // Re-bind from scratch — the tooltip may have appeared, disappeared,
        // or changed text since the last upsert. `change` events from DCS can
        // update a mark's caption mid-mission.
        existing.marker.unbindTooltip();
        const label = markLabelText(m);
        if (label) {
            existing.marker.bindTooltip(label, {
                direction: "top",
                offset: [0, -MARK_RADIUS_PX - 2],
                permanent: true,
                className: "mark-label",
            });
        }
        existing.data = m;
        applyMarkVisibility(existing);
        return;
    }
    const marker = buildMarkMarker(m);
    const entry = { marker, data: m, visible: false };
    marksById.set(m.id, entry);
    applyMarkVisibility(entry);
}

function removeMark(id) {
    const entry = marksById.get(id);
    if (!entry) return;
    if (entry.visible) entry.marker.remove();
    marksById.delete(id);
}

function applyMarksSnapshot(marks) {
    for (const { marker, visible } of marksById.values()) {
        if (visible) marker.remove();
    }
    marksById.clear();
    for (const m of marks) upsertMark(m);
}

// --- click-to-measure (BRA) --------------------------------------------------

// Great-circle math on the WGS-84 sphere (close enough — pilots round to nm).
function haversineNm(lat1, lon1, lat2, lon2) {
    const R = 6371000; // m
    const toRad = (d) => (d * Math.PI) / 180;
    const φ1 = toRad(lat1);
    const φ2 = toRad(lat2);
    const Δφ = toRad(lat2 - lat1);
    const Δλ = toRad(lon2 - lon1);
    const a = Math.sin(Δφ / 2) ** 2 + Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) ** 2;
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c * M_TO_NM;
}

function initialBearingDeg(lat1, lon1, lat2, lon2) {
    const toRad = (d) => (d * Math.PI) / 180;
    const φ1 = toRad(lat1);
    const φ2 = toRad(lat2);
    const Δλ = toRad(lon2 - lon1);
    const y = Math.sin(Δλ) * Math.cos(φ2);
    const x = Math.cos(φ1) * Math.sin(φ2) - Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
    const θ = (Math.atan2(y, x) * 180) / Math.PI;
    return (θ + 360) % 360;
}

// Apply declination to a true bearing. Positive declination (easterly) means
// magnetic north is east of true north, so a true bearing maps to a smaller
// magnetic bearing — hence subtraction. JS `%` keeps sign on negatives, so
// normalize into [0, 360) explicitly.
function trueToMagnetic(brgT, dec) {
    if (dec === null || dec === undefined) return brgT;
    return ((brgT - dec) % 360 + 360) % 360;
}

function formatBearing(brgDeg, dec) {
    const suffix = dec === null || dec === undefined ? "°T" : "°M";
    return `${String(Math.round(trueToMagnetic(brgDeg, dec)) % 360).padStart(3, "0")}${suffix}`;
}

function formatRange(rngNm) {
    // No zero-padding for distance (unlike bearings, where 3 digits is the
    // compass convention) — just the number of miles.
    return `${Math.round(rngNm)} nm`;
}

function formatBR(brgDeg, rngNm, dec) {
    return `${formatBearing(brgDeg, dec)} ${formatRange(rngNm)}`;
}

function pickReferenceBullseye() {
    // Player's own coalition wins; else first bullseye we have; else null.
    const playerUnit = findPlayerUnit();
    if (playerUnit) {
        const own = bullseyesByCoalition.get(playerUnit.coalition);
        if (own && shouldShowBullseye(own.data)) return own.data;
    }
    for (const entry of bullseyesByCoalition.values()) {
        if (shouldShowBullseye(entry.data)) return entry.data;
    }
    return null;
}

function buildRulerEndpointIcon() {
    const lines = `
    <line x1="3" y1="3" x2="13" y2="13" />
    <line x1="13" y1="3" x2="3" y2="13" />`;
    const svg = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16">
  <g stroke="${CASING_COLOR}" stroke-width="4" stroke-linecap="round" opacity="${CASING_OPACITY}">${lines}</g>
  <g stroke="${MEASURE_SELF_COLOR}" stroke-width="2" stroke-linecap="round">${lines}</g>
</svg>`.trim();
    return L.divIcon({
        className: "ruler-endpoint",
        html: svg,
        iconSize: [16, 16],
        iconAnchor: [8, 8],
    });
}

// Endpoint marker while tracking: a dashed ring + cross, pulsed via CSS so it
// reads as provisional vs the solid locked cross.
function buildTrackingEndpointIcon() {
    const cross = `
    <line x1="5" y1="5" x2="13" y2="13" />
    <line x1="13" y1="5" x2="5" y2="13" />`;
    const ring = `<circle cx="9" cy="9" r="7" fill="none" stroke-dasharray="3 3" />`;
    const svg = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 18 18" width="18" height="18">
  <g stroke="${CASING_COLOR}" stroke-width="4" stroke-linecap="round" opacity="${CASING_OPACITY}">${cross}${ring}</g>
  <g stroke="${MEASURE_SELF_COLOR}" stroke-width="2" stroke-linecap="round">${cross}${ring}</g>
</svg>`.trim();
    return L.divIcon({
        className: "ruler-endpoint ruler-endpoint-tracking",
        html: svg,
        iconSize: [18, 18],
        iconAnchor: [9, 9],
    });
}

// --- measure: map layers (lines + on-line labels) ----------------------------

function interpolateLatLng(a, b, t) {
    return L.latLng(a.lat + (b.lat - a.lat) * t, a.lng + (b.lng - a.lng) * t);
}

// Screen-pixel angle of segment a→b, in degrees, flipped to keep text upright.
// Pixel angle (not great-circle bearing) so it matches how the line is drawn;
// zoom/pan-invariant under Web Mercator, so it only needs recomputing when an
// endpoint moves (which already re-fires rebuildMeasureLayers).
function screenAngleDeg(a, b) {
    const pa = map.latLngToLayerPoint(a);
    const pb = map.latLngToLayerPoint(b);
    let deg = (Math.atan2(pb.y - pa.y, pb.x - pa.x) * 180) / Math.PI;
    if (deg > 90) deg -= 180;
    else if (deg < -90) deg += 180;
    return deg;
}

function makeMeasureLabel(latlng, text, extraClass, angleDeg, offsetPx = -12) {
    // A divIcon marker (not a permanent tooltip): tooltips fade in/out on
    // add/remove, so the teardown-and-rebuild on every cursor frame would leave
    // a pile of ghosting, half-faded copies during live tracking. Markers
    // add/remove synchronously. Centering: the 0-size icon sits at the point,
    // `.measure-label-anchor` translates -50%/-50% to center the box, and the
    // inner `.measure-label-pill` carries `rotate(...) translateY(...)` so it
    // rides along the line (negative offset above, positive below). `tooltipPane`
    // keeps it stacked above the measure lines, as the tooltip version was.
    const html =
        `<div class="measure-label-anchor"><span class="measure-label-pill ${extraClass}" ` +
        `style="transform: rotate(${angleDeg}deg) translateY(${offsetPx}px)">${text}</span></div>`;
    return L.marker(latlng, {
        icon: L.divIcon({ className: "measure-label", html, iconSize: [0, 0], iconAnchor: [0, 0] }),
        interactive: false,
        keyboard: false,
        pane: "tooltipPane",
    });
}

function rebuildMeasureLayers(targetLatLng, bullData, playerUnit, bullBR, selfOutBR, selfInBR, dec) {
    // Tear down the previous group, build a new one. Cheap — at most 2 lines +
    // 3 tooltips per measurement.
    if (measureState && measureState.layers) {
        measureState.layers.remove();
    }
    const group = L.layerGroup().addTo(map);
    if (bullData && bullBR) {
        const a = L.latLng(bullData.lat, bullData.lon);
        const b = targetLatLng;
        const color = COALITION_COLOR[bullData.coalition] || COALITION_COLOR[1];
        addCasedPolyline(group, [a, b], {
            color,
            weight: 3,
            opacity: 0.95,
            dashArray: "10 6",
        });
        const bullAngle = screenAngleDeg(a, b);
        const bullMid = interpolateLatLng(a, b, 0.5);
        // Same split as the self line: reciprocal bearings above, distance below.
        makeMeasureLabel(
            bullMid,
            `${formatBearing(bullBR.brg, dec)} / ${formatBearing(bullBR.brgIn, dec)}`,
            "measure-label-bull",
            bullAngle,
            -12,
        ).addTo(group);
        makeMeasureLabel(
            bullMid,
            formatRange(bullBR.rng),
            "measure-label-bull",
            bullAngle,
            12,
        ).addTo(group);
    }
    if (playerUnit && selfOutBR && selfInBR) {
        const a = L.latLng(playerUnit.lat, playerUnit.lon);
        const b = targetLatLng;
        addCasedPolyline(group, [a, b], {
            color: MEASURE_SELF_COLOR,
            weight: 3,
            opacity: 1.0,
            dashArray: "6 4",
        });
        const selfAngle = screenAngleDeg(a, b);
        const selfMid = interpolateLatLng(a, b, 0.5);
        // Split across the two sides to declutter: reciprocal bearings above the
        // line, the (shared) distance below — no prefixes, no repeated range.
        makeMeasureLabel(
            selfMid,
            `${formatBearing(selfOutBR.brg, dec)} / ${formatBearing(selfInBR.brg, dec)}`,
            "measure-label-self",
            selfAngle,
            -12,
        ).addTo(group);
        makeMeasureLabel(
            selfMid,
            formatRange(selfOutBR.rng),
            "measure-label-self",
            selfAngle,
            12,
        ).addTo(group);
    }
    if (measureState) measureState.layers = group;
}

function clearMeasure() {
    cancelMeasureRebuild();
    if (measureState) {
        measureState.marker.remove();
        if (measureState.layers) measureState.layers.remove();
        measureState = null;
    }
    measureEl.hidden = true;
    measureHintEl.hidden = true;
    measureAltEl.textContent = "…";
    measureGridEl.textContent = "—";
    measureGridRowEl.dataset.hasValue = "false";
    measureLatLonEl.textContent = "—";
    measureLatLonRowEl.dataset.hasValue = "false";
    measureBullEl.textContent = "—";
    measureSelfOutEl.textContent = "—";
    measureSelfInEl.textContent = "—";
    measureBullRowEl.dataset.hasValue = "false";
    measureSelfOutRowEl.dataset.hasValue = "false";
    measureSelfInRowEl.dataset.hasValue = "false";
    measureBullRowEl.hidden = false;
    measureSelfOutRowEl.hidden = false;
    measureSelfInRowEl.hidden = false;
}

// --- player declination (telemetry HUD) -------------------------------------

async function maybeRefreshPlayerDeclination(lat, lon) {
    const now = Date.now();
    if (now - playerDecState.fetchedAt < PLAYER_DEC_REFRESH_MS) return;
    // Claim the slot immediately so a flurry of unit_updates doesn't race.
    playerDecState.fetchedAt = now;
    try {
        const res = await fetch(`/api/declination?lat=${lat}&lon=${lon}`);
        if (!res.ok) return;
        const body = await res.json();
        if (typeof body.declination_deg === "number") {
            playerDecState.value = body.declination_deg;
            refreshTelemetry();
        }
    } catch (err) {
        console.warn("player declination fetch failed:", err);
    }
}

function refreshMeasureReadout() {
    if (!measureState) return;
    const { lat, lon, declinationDeg } = measureState;
    const target = L.latLng(lat, lon);

    const bull = pickReferenceBullseye();
    let bullBR = null;
    if (bull) {
        bullBR = {
            brg: initialBearingDeg(bull.lat, bull.lon, lat, lon),
            brgIn: initialBearingDeg(lat, lon, bull.lat, bull.lon), // reciprocal, for the on-line label
            rng: haversineNm(bull.lat, bull.lon, lat, lon),
        };
        measureBullLabelEl.textContent = `Bull (${COAL_NAMES[bull.coalition] || "?"})`;
        measureBullEl.textContent = formatBR(bullBR.brg, bullBR.rng, declinationDeg);
        measureBullRowEl.dataset.hasValue = "true";
        measureBullRowEl.hidden = false;
    } else {
        measureBullRowEl.dataset.hasValue = "false";
        measureBullRowEl.hidden = true;
    }

    const player = findPlayerUnit();
    let selfOutBR = null;
    let selfInBR = null;
    if (player) {
        selfOutBR = {
            brg: initialBearingDeg(player.lat, player.lon, lat, lon),
            rng: haversineNm(player.lat, player.lon, lat, lon),
        };
        selfInBR = {
            brg: initialBearingDeg(lat, lon, player.lat, player.lon),
            rng: selfOutBR.rng, // same great-circle distance
        };
        measureSelfOutEl.textContent = formatBR(selfOutBR.brg, selfOutBR.rng, declinationDeg);
        measureSelfInEl.textContent = formatBR(selfInBR.brg, selfInBR.rng, declinationDeg);
        measureSelfOutRowEl.dataset.hasValue = "true";
        measureSelfInRowEl.dataset.hasValue = "true";
        measureSelfOutRowEl.hidden = false;
        measureSelfInRowEl.hidden = false;
    } else {
        measureSelfOutRowEl.dataset.hasValue = "false";
        measureSelfInRowEl.dataset.hasValue = "false";
        measureSelfOutRowEl.hidden = true;
        measureSelfInRowEl.hidden = true;
    }

    rebuildMeasureLayers(target, bull, player, bullBR, selfOutBR, selfInBR, declinationDeg);
}

async function fetchElevation(lat, lon, reqId) {
    try {
        const res = await fetch(`/api/elevation?lat=${lat}&lon=${lon}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const body = await res.json();
        // Stale response (user clicked again before this one returned): drop.
        if (!measureState || measureState.elevReqId !== reqId) return;
        if (typeof body.elev_m === "number") {
            measureState.elevM = body.elev_m;
            const ft = Math.round(body.elev_m * M_TO_FT);
            measureAltEl.textContent = `${ft.toLocaleString("en-US")} ft`;
        } else {
            measureState.elevM = null;
            measureAltEl.textContent = "—";
        }
    } catch (err) {
        if (measureState && measureState.elevReqId === reqId) {
            measureState.elevM = null;
            measureAltEl.textContent = "—";
            console.warn("elevation fetch failed:", err);
        }
    }
}

async function fetchClickDeclination(lat, lon, reqId) {
    try {
        const res = await fetch(`/api/declination?lat=${lat}&lon=${lon}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const body = await res.json();
        if (!measureState || measureState.elevReqId !== reqId) return;
        if (typeof body.declination_deg === "number") {
            measureState.declinationDeg = body.declination_deg;
            refreshMeasureReadout();
        }
    } catch (err) {
        if (measureState && measureState.elevReqId === reqId) {
            console.warn("declination fetch failed:", err);
        }
    }
}

// Switches a marker's tooltip between "hover-show" (default) and "permanent"
// (sticky). Rebind is needed because Leaflet doesn't expose a clean in-place
// flip of the `permanent` option; the old tooltip is unbound and a new one
// with the toggled state takes its place, preserving content / direction /
// offset.
function setStickyTooltip(marker, sticky) {
    const tooltip = marker.getTooltip();
    if (!tooltip) return;
    const isSticky = tooltip.options.permanent === true;
    if (isSticky === sticky) return;
    const content = tooltip.getContent();
    const direction = tooltip.options.direction;
    const offset = tooltip.options.offset;
    marker.unbindTooltip();
    marker.bindTooltip(content, {
        direction,
        offset,
        permanent: sticky,
    });
    if (!sticky) {
        marker.closeTooltip();
    } else {
        // Sticky tooltips get a pale-yellow background so they read as
        // "pinned" vs the default hover. _container only exists after the
        // auto-open that permanent:true triggers.
        const el = marker.getTooltip()?._container;
        if (el) el.classList.add("mizmap-tooltip-sticky");
    }
}

// Thin click-handler wrapper that flips the marker's tooltip stickiness based
// on its current state. Used by bullseye markers, which don't participate in
// the unit-selection mechanism.
function toggleStickyTooltip(ev) {
    const marker = ev.target;
    const tooltip = marker.getTooltip();
    if (!tooltip) return;
    setStickyTooltip(marker, tooltip.options.permanent !== true);
}

// --- unit selection ---------------------------------------------------------
// One unit is selected at a time. Clicking a unit toggles its selection;
// clicking a different one swaps. Selection drives: the symbol's interior
// fill (white, F10-style), tooltip stickiness, and which unit the telemetry
// HUD shows.

function selectUnit(id) {
    if (selectedUnitId === id) return;
    if (selectedUnitId !== null) deselectUnit();
    const entry = unitsById.get(id);
    if (!entry) return;
    selectedUnitId = id;
    // Switching the selection stops any active follow ("another unit is
    // selected"). Unconditional so it also breaks a follow held without a prior
    // selection (e.g. nav-following the own-ship). The double-click path
    // re-establishes follow right after this returns.
    setFollow(null);
    setStickyTooltip(entry.marker, true);
    refreshUnitIcon(entry); // key includes selection → rebuilds (fog-aware)
    refreshTelemetry();
    updateRecenterControlVisibility();
    // Focus mode pins the selected group's route to the map.
    if (FILTERS.routesMode === "focus") applyRouteVisibilityAll();
}

function deselectUnit() {
    if (selectedUnitId === null) return;
    const entry = unitsById.get(selectedUnitId);
    selectedUnitId = null; // clear before refresh so the icon comes back unselected
    setFollow(null); // deselecting the followed unit stops following
    if (entry) {
        setStickyTooltip(entry.marker, false);
        refreshUnitIcon(entry);
    }
    refreshTelemetry();
    updateRecenterControlVisibility();
    if (FILTERS.routesMode === "focus") applyRouteVisibilityAll();
}

function handleUnitClick(id) {
    if (selectedUnitId === id) deselectUnit();
    else selectUnit(id);
}

// Desktop middle-click state machine: idle/frozen → start tracking; tracking →
// lock at the exact click point. Right-click (clearMeasure) exits from any state.
function handleMeasureClick(latlng) {
    if (FILTERS.layers.measure !== true) return;
    if (measureState && measureState.mode === "tracking") freezeMeasure(latlng);
    else beginTracking(latlng);
}

function beginTracking(latlng) {
    setMeasureTarget(latlng, "tracking");
}

function freezeMeasure(latlng) {
    setMeasureTarget(latlng, "frozen");
}

// (Re)build measureState + panel for a target point. `mode` "tracking" keeps the
// readout true and skips the Eval fetches (one per cursor move would be brutal);
// "frozen" locks the point and fetches elevation + declination (→ magnetic).
function setMeasureTarget(latlng, mode) {
    cancelMeasureRebuild();
    const lat = latlng.lat;
    const lon = latlng.lng;
    const tracking = mode === "tracking";
    if (measureState) {
        measureState.marker.remove();
        if (measureState.layers) measureState.layers.remove();
    }
    const marker = L.marker([lat, lon], {
        icon: tracking ? buildTrackingEndpointIcon() : buildRulerEndpointIcon(),
        interactive: false,
        keyboard: false,
    }).addTo(map);
    const reqId = ++measureReqCounter;
    measureState = {
        lat,
        lon,
        mode,
        marker,
        elevReqId: reqId,
        layers: null,
        elevM: null,
        declinationDeg: null,
    };
    measureEl.hidden = false;
    measureHintEl.hidden = !tracking;
    measureAltEl.textContent = "…";
    updateMeasurePoint(lat, lon);
    refreshMeasureReadout();
    if (!tracking) {
        fetchElevation(lat, lon, reqId);
        fetchClickDeclination(lat, lon, reqId);
    }
}

// Live cursor follow while tracking — lightweight per-move update (no marker /
// state recreation), with the line/label rebuild coalesced to one rAF.
function updateTrackingTarget(latlng) {
    if (!measureState || measureState.mode !== "tracking") return;
    measureState.lat = latlng.lat;
    measureState.lon = latlng.lng;
    measureState.marker.setLatLng(latlng);
    updateMeasurePoint(latlng.lat, latlng.lng);
    scheduleMeasureRebuild();
}

// MGRS + L/L of the target point. Pure function of the point (unlike the
// bearings, which depend on the live player/bull), so set directly here.
function updateMeasurePoint(lat, lon) {
    const grid = formatMgrs(lat, lon);
    measureGridEl.textContent = grid;
    measureGridRowEl.dataset.hasValue = grid !== "—" ? "true" : "false";
    measureLatLonEl.textContent = formatLatLonDdm(lat, lon);
    measureLatLonRowEl.dataset.hasValue = "true";
}

function scheduleMeasureRebuild() {
    if (measureRebuildRaf) return;
    measureRebuildRaf = requestAnimationFrame(() => {
        measureRebuildRaf = 0;
        if (measureState) refreshMeasureReadout();
    });
}

function cancelMeasureRebuild() {
    if (measureRebuildRaf) {
        cancelAnimationFrame(measureRebuildRaf);
        measureRebuildRaf = 0;
    }
}

// --- copy buttons -----------------------------------------------------------

function copyTextFor(target) {
    if (!measureState) return null;
    if (target === "grid") {
        const g = measureGridEl.textContent;
        return g && g !== "—" ? g : null;
    }
    if (target === "latlon") {
        const v = measureLatLonEl.textContent;
        return v && v !== "—" ? v : null;
    }
    const altFt =
        typeof measureState.elevM === "number"
            ? Math.round(measureState.elevM * M_TO_FT)
            : null;
    const altStr = altFt === null ? "—" : String(altFt);
    const valueEl =
        target === "bull"
            ? measureBullEl
            : target === "self-out"
              ? measureSelfOutEl
              : target === "self-in"
                ? measureSelfInEl
                : null;
    if (!valueEl || valueEl.textContent === "—") return null;
    // Parse "274° 045 nm" → "274/045" for compact slash format.
    const match = valueEl.textContent.match(/^(\d{3})°\s+(\d{3})\s+nm$/);
    const compact = match ? `${match[1]}/${match[2]}` : valueEl.textContent;
    const tag =
        target === "bull"
            ? `BULL (${pickReferenceBullseye()?.coalition === 3 ? "Blue" : "Red"})`
            : target === "self-out"
              ? "SELF→TGT"
              : "TGT→SELF";
    return `${tag} ${compact}/${altStr}`;
}

async function handleCopyClick(ev) {
    const btn = ev.currentTarget;
    const text = copyTextFor(btn.dataset.copy);
    if (!text) return;
    try {
        await navigator.clipboard.writeText(text);
        btn.classList.add("copied");
        setTimeout(() => btn.classList.remove("copied"), 900);
    } catch (err) {
        console.warn("clipboard write failed:", err);
    }
}

function applyRoutesSnapshot(routes) {
    // Routes are static for the mission — full replace each snapshot.
    for (const { layer, visible } of routesByGroupId.values()) {
        if (visible) layer.remove();
    }
    routesByGroupId.clear();
    for (const r of routes) {
        if (!r.points || r.points.length === 0) continue;
        const layer = buildRouteLayer(r);
        const entry = { layer, data: r, visible: false };
        routesByGroupId.set(r.group_id, entry);
        applyRouteVisibility(entry);
    }
    // Route indices changed (mission load / restart); any manual WP selection
    // would now point at a different real waypoint. Drop back to auto-pick.
    navWpIndexOverride = null;
}

function connectWebSocket() {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${proto}//${window.location.host}/ws`;
    let backoff = 1000;
    let ws;

    function open() {
        ws = new WebSocket(url);

        ws.addEventListener("open", () => {
            setStatus(wsStatusEl, true, "WebSocket");
            backoff = 1000;
        });

        ws.addEventListener("close", () => {
            setStatus(wsStatusEl, false, "WebSocket");
            setTimeout(open, backoff);
            backoff = Math.min(backoff * 2, 15000);
        });

        ws.addEventListener("error", () => {
            // 'close' will follow — handle reconnect there.
        });

        ws.addEventListener("message", (ev) => {
            let msg;
            try {
                msg = JSON.parse(ev.data);
            } catch {
                console.warn("non-JSON ws message", ev.data);
                return;
            }
            switch (msg.type) {
                case "hello":
                    if (msg.version) versionEl.textContent = `v${msg.version}`;
                    break;
                case "grpc_status":
                    applyGrpcStatus(msg);
                    break;
                case "units_snapshot":
                    applySnapshot(msg.units || []);
                    refreshTelemetry();
                    break;
                case "unit_update":
                    upsertUnit(msg.unit);
                    refreshTelemetry();
                    refreshVisibilityIfPlayerChanged();
                    maybeAutoCenterOnOwnShip();
                    updateRecenterControlVisibility();
                    // Nav panel data (WP/BRG/DIST/ETA) tracks the own-ship every
                    // tick, independent of map-follow.
                    if (navModeOn) refreshNavPanel();
                    // Map-follow: keep the followed unit centered as it moves.
                    // animate:false — unit updates arrive faster than a smooth
                    // pan could complete, so any animation would stutter.
                    if (followedUnitId !== null && msg.unit.id === followedUnitId) {
                        map.panTo([msg.unit.lat, msg.unit.lon], { animate: false });
                    }
                    // Player moved → Self row in measure panel needs an update.
                    if (measureState) refreshMeasureReadout();
                    break;
                case "unit_gone":
                    removeUnit(msg.id);
                    refreshTelemetry();
                    refreshVisibilityIfPlayerChanged();
                    updateRecenterControlVisibility();
                    break;
                case "mission_routes_snapshot":
                    applyRoutesSnapshot(msg.routes || []);
                    if (navModeOn) refreshNavPanel();
                    break;
                case "bullseyes_snapshot":
                    applyBullseyesSnapshot(msg.bullseyes || []);
                    break;
                case "airbases_snapshot":
                    applyAirbasesSnapshot(msg.airbases || []);
                    break;
                case "runways_snapshot":
                    applyRunwaysSnapshot(msg.runways || []);
                    break;
                case "navaids_snapshot":
                    applyNavaidsSnapshot(msg.navaids || []);
                    break;
                case "marks_snapshot":
                    applyMarksSnapshot(msg.marks || []);
                    break;
                case "mark_added":
                    if (msg.mark) upsertMark(msg.mark);
                    break;
                case "mark_removed":
                    removeMark(msg.id);
                    break;
                case "fog_snapshot":
                    applyFogSnapshot(msg);
                    break;
                default:
                    console.debug("unhandled message", msg);
            }
        });
    }

    open();
}

(async () => {
    decodeHash();
    // Precedence: URL hash > localStorage > default. After resolution, write
    // through to localStorage so a subsequent hash-less load inherits the
    // active choice (including the one a shared link carried in).
    if (!trailLengthSetByHash) {
        const stored = readTrailLengthFromStorage();
        if (stored !== null) FILTERS.trailLengthSec = stored;
    }
    writeTrailLengthToStorage(FILTERS.trailLengthSec);
    if (!routesModeSetByHash) {
        const storedMode = readRoutesModeFromStorage();
        if (storedMode !== null) FILTERS.routesMode = storedMode;
    }
    writeRoutesModeToStorage(FILTERS.routesMode);
    initNavPanelRefs();
    navModeOn = readNavModeFromStorage();
    if (navEls.data) navEls.data.hidden = !navModeOn;
    if (navEls.toggle) navEls.toggle.checked = navModeOn;
    syncCheckboxesFromFilters();
    wireFilterCheckboxes();
    syncFogControls();
    wireFogControls();
    // Re-fade/expire fog ghosts between snapshots (snapshots only refresh the
    // currently-detected set; aging is purely time-based). Cheap no-op unless
    // the lens is on with a memory window.
    setInterval(() => {
        if (FILTERS.fog.on && fogReceived && FILTERS.fog.memorySec > 0) applyFogAll();
    }, FOG_TICK_MS);
    const config = await loadConfig();
    map = buildMap(config);
    // Measurement was on left-click in earlier versions; moved to middle-click
    // so left-click is free to toggle sticky tooltips on markers. Browsers
    // trigger autoscroll on middle-button mousedown by default — preventDefault
    // there suppresses it; the actual measurement fires on auxclick after the
    // mouseup completes. First middle-click starts tracking (target follows the
    // cursor); the second locks it.
    const container = map.getContainer();
    L.DomEvent.on(container, "mousedown", (ev) => {
        if (ev.button === 1) ev.preventDefault();
    });
    L.DomEvent.on(container, "auxclick", (ev) => {
        if (ev.button !== 1) return;
        ev.preventDefault();
        handleMeasureClick(map.mouseEventToLatLng(ev));
    });
    map.on("contextmenu", (ev) => {
        // Right-click clears measurement and suppresses the default browser menu.
        L.DomEvent.preventDefault(ev.originalEvent);
        clearMeasure();
    });
    // Live MGRS readout of the point under the cursor. Hover-only — touch has
    // no hover (and a stray tap-driven mousemove would leave the pill stuck on),
    // so wire it only on fine-pointer/hover devices. The measure panel's MGRS
    // row is the touch equivalent.
    if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
        map.on("mousemove", (ev) => {
            cursorMgrsEl.textContent = formatMgrs(ev.latlng.lat, ev.latlng.lng);
            cursorLatLonEl.textContent = formatLatLonDdm(ev.latlng.lat, ev.latlng.lng);
            cursorReadoutEl.hidden = false;
            updateTrackingTarget(ev.latlng); // no-op unless a measurement is tracking
        });
        map.on("mouseout", () => {
            cursorReadoutEl.hidden = true;
        });
    }
    measureClearBtn.addEventListener("click", clearMeasure);
    for (const btn of document.querySelectorAll(".measure-copy")) {
        btn.addEventListener("click", handleCopyClick);
    }
    wireCollapsibleSections();
    wireKneeboardControls();
    wireSettings();
    connectWebSocket();
})();

// --- settings panel ---------------------------------------------------------
// Maps the editable setting keys (as the backend names them) to their input
// element ids. POST/GET use the same keys, so this is the single source of
// truth for which fields the panel exposes.
const SETTINGS_FIELDS = {
    dcs_install_dir: "setDcsDir",
    http_port: "setHttpPort",
    http_host: "setHttpHost",
    grpc_host: "setGrpcHost",
    grpc_port: "setGrpcPort",
};
let settingsMeta = {}; // key -> { value, env_locked, restart_required }

async function openSettings() {
    const modal = document.getElementById("settingsModal");
    if (!modal) return;
    const banner = document.getElementById("settingsBanner");
    const msg = document.getElementById("settingsMsg");
    if (banner) { banner.hidden = true; banner.textContent = ""; }
    if (msg) { msg.textContent = ""; msg.className = "settings-msg"; }
    try {
        const res = await fetch("/api/settings");
        const data = await res.json();
        settingsMeta = data.settings || {};
        for (const [key, id] of Object.entries(SETTINGS_FIELDS)) {
            const meta = settingsMeta[key] || {};
            const el = document.getElementById(id);
            if (!el) continue;
            el.value = meta.value ?? "";
            el.disabled = !!meta.env_locked;
            const field = el.closest(".settings-field");
            const existing = field?.querySelector(".settings-locked");
            if (meta.env_locked && field && !existing) {
                const n = document.createElement("span");
                n.className = "settings-hint settings-locked";
                n.textContent = "Pinned by an environment variable.";
                field.appendChild(n);
            } else if (!meta.env_locked && existing) {
                existing.remove();
            }
        }
        const dcsInput = document.getElementById("setDcsDir");
        const dcsHint = document.getElementById("setDcsHint");
        const detected = data.dcs_install_dir_detected;
        if (dcsInput) dcsInput.placeholder = detected ? `auto-detected: ${detected}` : "e.g. C:\\DCS";
        if (dcsHint) {
            dcsHint.textContent = detected
                ? "Leave blank to use the auto-detected path."
                : "Not auto-detected — set your DCS World install folder for the Navaids layer.";
        }
    } catch (err) {
        console.warn("settings load failed:", err);
    }
    modal.hidden = false;
}

function closeSettings() {
    const modal = document.getElementById("settingsModal");
    if (modal) modal.hidden = true;
}

async function saveSettings() {
    // Persist ONLY fields the user actually changed. Writing every visible
    // field would bake current defaults into config.toml — cluttering it and
    // freezing the user at today's defaults (a future default change wouldn't
    // reach them). Env-locked keys are never sent (the server rejects them).
    const payload = {};
    for (const [key, id] of Object.entries(SETTINGS_FIELDS)) {
        if (settingsMeta[key]?.env_locked) continue;
        const el = document.getElementById(id);
        if (!el) continue;
        const current = String(settingsMeta[key]?.value ?? "");
        const next = el.value.trim();
        if (next !== current) payload[key] = next;
    }
    const msg = document.getElementById("settingsMsg");
    const banner = document.getElementById("settingsBanner");
    if (Object.keys(payload).length === 0) {
        if (msg) { msg.textContent = "No changes."; msg.className = "settings-msg"; }
        return;
    }
    try {
        const res = await fetch("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok || data.saved === false) {
            if (msg) {
                msg.textContent = (data.errors || ["save failed"]).join("; ");
                msg.className = "settings-msg settings-msg-error";
            }
            return;
        }
        if (msg) { msg.textContent = "Saved."; msg.className = "settings-msg settings-msg-ok"; }
        if (banner && data.restart_required && data.restart_required.length) {
            banner.textContent = `Restart MizMap to apply: ${data.restart_required.join(", ")}.`;
            banner.hidden = false;
        }
    } catch (err) {
        if (msg) {
            msg.textContent = `Save failed: ${err}`;
            msg.className = "settings-msg settings-msg-error";
        }
    }
}

function wireSettings() {
    const btn = document.getElementById("settingsBtn");
    const closeBtn = document.getElementById("settingsClose");
    const saveBtn = document.getElementById("settingsSave");
    const modal = document.getElementById("settingsModal");
    if (btn) btn.addEventListener("click", openSettings);
    if (closeBtn) closeBtn.addEventListener("click", closeSettings);
    if (saveBtn) saveBtn.addEventListener("click", saveSettings);
    // Click on the dim backdrop (not the card) closes.
    if (modal) modal.addEventListener("click", (e) => { if (e.target === modal) closeSettings(); });
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && modal && !modal.hidden) closeSettings();
    });
    // Tray "Settings…" opens the viewer with ?settings=1.
    if (new URLSearchParams(window.location.search).get("settings") === "1") openSettings();
}

// --- kneeboard touch controls ----------------------------------------------
// `kbMeasureArmed` gates the next map click into the measure tool. The button
// stays "armed" until a click lands or the user disarms it. Visual state lives
// on the button via the `kb-armed` class. No-op when the buttons are hidden
// (i.e. main view).
let kbMeasureArmed = false;

function readSectionStateFromStorage() {
    try {
        const raw = localStorage.getItem(SECTIONS_LS_KEY);
        const parsed = raw ? JSON.parse(raw) : null;
        return parsed && typeof parsed === "object" ? parsed : {};
    } catch {
        // Private-mode browsers can throw or store junk. Treat as "no preference."
        return {};
    }
}

function writeSectionStateToStorage(state) {
    try {
        localStorage.setItem(SECTIONS_LS_KEY, JSON.stringify(state));
    } catch {
        // localStorage may be unavailable (private mode, quota). Best-effort.
    }
}

// Filter-panel groups are disclosure sections: clicking a header collapses or
// expands its body. HTML carries the smart defaults; a remembered choice (per
// section) wins over the default and persists across reloads.
function wireCollapsibleSections() {
    const saved = readSectionStateFromStorage();
    for (const section of document.querySelectorAll("#filters .filter-section")) {
        const key = section.dataset.section;
        const header = section.querySelector(".filter-section-header");
        if (!key || !header) continue;
        if (key in saved) {
            section.classList.toggle("collapsed", saved[key] === true);
        }
        header.setAttribute("aria-expanded", String(!section.classList.contains("collapsed")));
        header.addEventListener("click", () => {
            const collapsed = section.classList.toggle("collapsed");
            header.setAttribute("aria-expanded", String(!collapsed));
            const state = readSectionStateFromStorage();
            state[key] = collapsed;
            writeSectionStateToStorage(state);
        });
    }
}

function wireKneeboardControls() {
    const menuBtn = document.getElementById("kbMenuBtn");
    const filtersPanel = document.getElementById("filters");
    if (menuBtn && filtersPanel) {
        // Tablet/touch: panel is hidden by default → click adds .kb-open to
        // slide it in. Desktop: panel is visible by default → click adds
        // .kb-closed to hide it. matchMedia checked per-click so a window
        // resize across the breakpoint picks up the right semantics.
        const tabletQuery = window.matchMedia("(max-width: 900px), (pointer: coarse)");
        menuBtn.addEventListener("click", () => {
            const cls = tabletQuery.matches ? "kb-open" : "kb-closed";
            filtersPanel.classList.toggle(cls);
        });
    }
    const measureBtn = document.getElementById("kbMeasureBtn");
    if (measureBtn) {
        measureBtn.addEventListener("click", (ev) => {
            ev.stopPropagation();
            kbMeasureArmed = !kbMeasureArmed;
            measureBtn.classList.toggle("kb-armed", kbMeasureArmed);
        });
    }
    if (map) {
        map.on("click", (ev) => {
            if (!kbMeasureArmed) return;
            // Touch has no cursor to follow, so the tap places a locked
            // measurement directly (one-shot, as before the tracking model).
            if (FILTERS.layers.measure === true) freezeMeasure(ev.latlng);
            kbMeasureArmed = false;
            measureBtn?.classList.remove("kb-armed");
        });
    }
}
