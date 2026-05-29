"""Capture landing-page screenshots from the running MizMap viewer.

Drives the system Chrome via Playwright (channel='chrome' — no Playwright
chromium download). Saves PNGs to docs/assets/.

Run via:
    uv run --with playwright python scripts/capture_landing_shots.py [shot_name ...]

If no shot names are passed, captures all. Useful names: hero, symbols, hud,
bra, routes, marks, threats, nav.

Assumes `mizmap serve` is running on http://localhost:8766 with a live mission.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Callable

from playwright.sync_api import Page, sync_playwright

MizMap = "http://localhost:8766"
REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS = REPO_ROOT / "docs" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

# Injected BEFORE page scripts. Polls until Leaflet is loaded, then patches
# Map.prototype.addLayer so we can grab the module-private map instance the
# first time it's used (which happens during initial map setup).
INIT_SCRIPT = """
(function () {
  function patch() {
    if (!window.L || !window.L.Map || window.__patched) return false;
    window.__patched = true;
    var orig = window.L.Map.prototype.addLayer;
    window.L.Map.prototype.addLayer = function () {
      window.__leafletMap = this;
      return orig.apply(this, arguments);
    };
    return true;
  }
  if (!patch()) {
    var id = setInterval(function () { if (patch()) clearInterval(id); }, 10);
  }
})();
"""

# Wait for the WS snapshot to populate the map before we start posing.
HYDRATE_JS = """
async () => {
  const start = Date.now();
  while (Date.now() - start < 10000) {
    const m = document.querySelectorAll('.leaflet-marker-pane > *').length;
    const haveMap = !!window.__leafletMap;
    if (m > 0 && haveMap) return m;
    await new Promise(r => setTimeout(r, 100));
  }
  return 0;
}
"""

# Center the map and wait for tiles to settle.
def set_view(page: Page, lat: float, lon: float, zoom: int) -> None:
    page.evaluate(
        "({lat, lon, zoom}) => window.__leafletMap.setView([lat, lon], zoom, {animate: false})",
        {"lat": lat, "lon": lon, "zoom": zoom},
    )
    # Wait briefly for tile loading + symbol re-layout.
    page.wait_for_timeout(1500)


def close_filter_panel(page: Page) -> None:
    page.evaluate(
        """() => {
          const filters = document.getElementById('filters');
          if (!filters) return;
          const desktop = !window.matchMedia('(max-width: 900px), (pointer: coarse)').matches;
          if (desktop) filters.classList.add('kb-closed');
          else filters.classList.remove('kb-open');
        }"""
    )
    page.wait_for_timeout(300)


def open_filter_panel(page: Page) -> None:
    page.evaluate(
        """() => {
          const filters = document.getElementById('filters');
          if (!filters) return;
          filters.classList.remove('kb-closed');
          filters.classList.add('kb-open');
        }"""
    )
    page.wait_for_timeout(200)


# Filter inventory (matches web/index.html):
#   coalition: 1=neutral 2=red 3=blue
#   category:  1=plane 2=helo 3=ground 4=ship 5=train
#   layers:    routes, bullseyes, marks, measure, threats, vectors, trails
def set_filters(page: Page, on: dict) -> None:
    """Force exactly the listed filters ON, everything else OFF.

    `on` is a dict like:
        {"coalition": [2, 3], "category": [1, 3], "layers": ["routes"]}
    Unspecified groups default to "all on" (e.g. omitting "coalition" keeps
    all three coalitions visible). Pass an empty list to turn a whole group
    off (e.g. `"layers": []` disables every overlay).
    """
    spec = {
        "coalition": on.get("coalition", [1, 2, 3]),
        "category": on.get("category", [1, 2, 3, 4, 5]),
        "layers": on.get("layers", ["routes", "bullseyes", "marks", "measure",
                                    "threats", "vectors", "trails"]),
    }
    page.evaluate(
        """(spec) => {
          const groups = {coalition: 'coalition', category: 'category', layers: 'layers'};
          for (const [group, wanted] of Object.entries(spec)) {
            const wantedSet = new Set(wanted.map(String));
            document.querySelectorAll(
              `input[type=checkbox][data-filter='${groups[group]}']`
            ).forEach((cb) => {
              const want = wantedSet.has(String(cb.dataset.value));
              if (cb.checked !== want) {
                cb.checked = want;
                cb.dispatchEvent(new Event('change', {bubbles: true}));
              }
            });
          }
        }""",
        spec,
    )
    # Let the map re-render with filter changes applied.
    page.wait_for_timeout(700)


def shot_default(page: Page) -> None:
    close_filter_panel(page)


def shot_hero(page: Page) -> None:
    close_filter_panel(page)
    # Hero deliberately leaves all layers on — busy is good here.
    set_view(page, 29.10, 58.42, 10)


def shot_filters(page: Page) -> None:
    # Filter panel open + a map view behind it so the "what's visible" claim
    # has a backdrop. Keep the map reasonably busy (units + threat rings +
    # routes) so the toggles feel like they actually do something.
    open_filter_panel(page)
    set_filters(page, {})  # all on (default), in case a previous shot left state
    set_view(page, 29.10, 58.42, 10)


def shot_symbols(page: Page) -> None:
    close_filter_panel(page)
    # Turn off ALL layers/overlays — clean focus on the milsymbol icons.
    set_filters(page, {"layers": []})
    # Find the densest cluster of unit symbols, zoom in tight.
    info = page.evaluate(
        """() => {
          const layers = Object.values(window.__leafletMap._layers || {});
          const units = layers.filter(l =>
            l._latlng && l._icon && l._icon.classList && l._icon.classList.contains('milsymbol')
          );
          if (units.length === 0) return null;
          const buckets = new Map();
          for (const u of units) {
            const key = Math.round(u._latlng.lat / 0.05) + ',' + Math.round(u._latlng.lng / 0.05);
            if (!buckets.has(key)) buckets.set(key, []);
            buckets.get(key).push(u._latlng);
          }
          let bestKey = null, bestCount = 0;
          for (const [k, v] of buckets) {
            if (v.length > bestCount) { bestCount = v.length; bestKey = k; }
          }
          const pts = buckets.get(bestKey);
          const lat = pts.reduce((s, p) => s + p.lat, 0) / pts.length;
          const lng = pts.reduce((s, p) => s + p.lng, 0) / pts.length;
          return {lat, lon: lng, count: bestCount};
        }"""
    )
    print(f"  [symbols] cluster: {info}")
    if info:
        page.evaluate(
            """({lat, lon}) => {
              window.__leafletMap.setView([lat, lon], 15, {animate: false});
            }""",
            {"lat": info["lat"], "lon": info["lon"]},
        )
        page.wait_for_timeout(1500)


def shot_hud(page: Page) -> None:
    # Wide view; HUD bottom strip captured via clip box.
    close_filter_panel(page)
    # Keep blue (own-ship coalition) friendlies on; everything else off so the
    # map behind the HUD reads as a clean tactical surface.
    set_filters(page, {"coalition": [3], "category": [1, 2], "layers": []})
    set_view(page, 29.18, 58.71, 12)


def shot_bra(page: Page) -> None:
    """Draw a measure line by middle-clicking two points on the map."""
    close_filter_panel(page)
    # Keep only what's relevant: units + the measurement overlay.
    set_filters(page, {"layers": ["measure"]})
    set_view(page, 29.18, 58.71, 12)
    page.wait_for_timeout(500)
    # Two points framing the ruler in the image's center.
    p1 = (650, 520)
    p2 = (1000, 380)
    for x, y in (p1, p2):
        page.mouse.move(x, y)
        page.mouse.down(button="middle")
        page.mouse.up(button="middle")
        page.wait_for_timeout(300)


def shot_routes(page: Page) -> None:
    close_filter_panel(page)
    # Section is titled "Flight plan + F10 marks" — enable both overlays.
    set_filters(page, {"coalition": [3], "category": [1, 2], "layers": ["routes", "marks"]})
    info = page.evaluate(
        """() => {
          const layers = Object.values(window.__leafletMap._layers || {});
          // Route polylines are L.polyline objects with _latlngs (an array).
          const routes = layers.filter(l =>
            Array.isArray(l._latlngs) && l._latlngs.length > 1 && typeof l.getBounds === 'function'
          );
          if (routes.length === 0) return null;
          // Pick the route whose closest waypoint is nearest to any mark — so
          // both fit naturally in the viewport. Falls back to the longest route
          // when no marks are present.
          const marks = layers.filter(l => l.options && l.options.pane === 'dcmMarksPane' && l._latlng);
          let chosen;
          if (marks.length > 0) {
            const m = marks[0]._latlng;
            const dist2 = (a, b) => {
              const dx = a.lng - b.lng, dy = a.lat - b.lat;
              return dx*dx + dy*dy;
            };
            chosen = routes.map(r => ({
              r,
              d: Math.min.apply(Math, r._latlngs.map(ll => dist2(ll, m)))
            })).sort((a, b) => a.d - b.d)[0].r;
          } else {
            chosen = routes.sort((a, b) => {
              const ba = a.getBounds(), bb = b.getBounds();
              const da = ba.getNorth() - ba.getSouth() + (ba.getEast() - ba.getWest());
              const db = bb.getNorth() - bb.getSouth() + (bb.getEast() - bb.getWest());
              return db - da;
            })[0];
          }
          // Union the chosen route's bounds with any visible mark so both fit.
          const b = chosen.getBounds();
          let south = b.getSouth(), north = b.getNorth();
          let west  = b.getWest(),  east  = b.getEast();
          for (const m of marks) {
            const ll = m._latlng;
            south = Math.min(south, ll.lat); north = Math.max(north, ll.lat);
            west  = Math.min(west,  ll.lng); east  = Math.max(east,  ll.lng);
          }
          return {south, west, north, east, markCount: marks.length};
        }"""
    )
    print(f"  [routes] bounds: {info}")
    if info:
        page.evaluate(
            """(b) => {
              window.__leafletMap.fitBounds(
                [[b.south, b.west], [b.north, b.east]],
                {animate: false, padding: [80, 80]}
              );
            }""",
            info,
        )
        page.wait_for_timeout(1500)


def shot_marks(page: Page) -> None:
    close_filter_panel(page)
    set_filters(page, {"coalition": [3], "category": [1, 2], "layers": ["marks"]})
    page.wait_for_timeout(500)
    info = page.evaluate(
        """() => {
          const layers = Object.values(window.__leafletMap._layers || {});
          const marks = layers.filter(l => l.options && l.options.pane === 'dcmMarksPane' && l._latlng);
          if (marks.length === 0) return {ok: false, count: layers.length};
          const m = marks[0];
          return {ok: true, lat: m._latlng.lat, lon: m._latlng.lng, count: marks.length};
        }"""
    )
    print(f"  [marks] {info}")
    if info.get("ok"):
        page.evaluate(
            """({lat, lon}) => {
              window.__leafletMap.setView([lat, lon], 14, {animate: false});
            }""",
            {"lat": info["lat"], "lon": info["lon"]},
        )
        page.wait_for_timeout(2000)


def shot_threats(page: Page) -> None:
    close_filter_panel(page)
    # Just the red ground units (SAMs etc) + their threat rings. Nothing else.
    set_filters(page, {"coalition": [2], "category": [3], "layers": ["threats"]})
    # Threat rings are L.circle with fill:none and stroke-dasharray (per main.js).
    info = page.evaluate(
        """() => {
          const paths = Array.from(document.querySelectorAll('.leaflet-overlay-pane path'));
          // dashed-stroke + no-fill = threat ring overlay
          const rings = paths.filter(p => {
            const s = window.getComputedStyle(p);
            const dash = p.getAttribute('stroke-dasharray');
            return s.fill === 'none' && dash && dash !== 'none';
          });
          if (rings.length === 0) return null;
          // Pick the median-sized ring (avoid the biggest extreme + tiny ones)
          const sorted = rings.map(r => {
            const b = r.getBoundingClientRect();
            return {el: r, w: b.width, x: b.left + b.width/2, y: b.top + b.height/2};
          }).sort((a, b) => a.w - b.w);
          // Filter out tiny ones (off-screen / shrunken)
          const reasonable = sorted.filter(r => r.w > 80);
          const pick = reasonable[Math.floor(reasonable.length / 2)] || sorted[sorted.length - 1];
          return {x: pick.x, y: pick.y, w: pick.w};
        }"""
    )
    if info:
        page.evaluate(
            """({x, y}) => {
              const ll = window.__leafletMap.containerPointToLatLng([x, y]);
              window.__leafletMap.setView(ll, 11, {animate: false});
            }""",
            {"x": info["x"], "y": info["y"]},
        )
        page.wait_for_timeout(1500)
    else:
        # Fallback: known SAM cluster center near Bam, SW
        set_view(page, 28.96, 58.30, 11)


def shot_nav(page: Page) -> None:
    # Click the NAV toggle to engage nav mode + show the next-waypoint panel.
    close_filter_panel(page)
    set_filters(page, {"coalition": [3], "category": [1], "layers": ["routes"]})
    set_view(page, 29.18, 58.71, 13)
    page.evaluate("document.getElementById('navToggle').click()")
    page.wait_for_timeout(1500)


def shot_fog(page: Page) -> None:
    """Fog-of-war lens from the Red viewpoint: a degraded type-unknown frame +
    dashed uncertainty ring (ENFIELD11) and a faded last-known ghost
    (ENFIELD12), undetected units hidden.

    Needs the dev mock (it serves the degraded/ghost detection picture); the
    state is time-varying, so we frame the Blue jets and break the instant a
    `.fog-ghost` marker appears — the start of the ~20 s ghost window.
    """
    close_filter_panel(page)
    set_filters(page, {"layers": []})  # units only; no overlays/vectors/trails
    # Fog isn't a `layers` checkbox — enable it + pick the Red viewpoint directly.
    page.evaluate(
        """() => {
          const t = document.getElementById('fogToggle');
          if (t && !t.checked) { t.checked = true; t.dispatchEvent(new Event('change', {bubbles: true})); }
          const vp = document.getElementById('fogViewpointSel');
          if (vp) { vp.value = '2'; vp.dispatchEvent(new Event('change', {bubbles: true})); }
        }"""
    )
    page.wait_for_timeout(800)
    # Center on the amber uncertainty ring so it sits centred and fills the
    # frame (it's the large, signature fog element); the small symbols read as
    # contacts within it. Break the instant a last-known ghost appears.
    framed = False
    for _ in range(45):
        framed = page.evaluate(
            """() => {
              const map = window.__leafletMap;
              if (!map) return false;
              const layers = Object.values(map._layers || {});
              // entry.fogRing is an L.circle drawn in the fog ring colour.
              const ring = layers.find(l => l.options && l.options.color === '#d8b45a'
                && l._latlng && typeof l.getRadius === 'function');
              const units = layers.filter(l => l._latlng && l._icon && l._icon.classList
                && l._icon.classList.contains('milsymbol'));
              if (ring) map.setView(ring._latlng, 13, {animate: false});
              else if (units.length >= 1) map.setView(units[0]._latlng, 13, {animate: false});
              const ghost = layers.find(l => l._icon && l._icon.classList
                && l._icon.classList.contains('fog-ghost'));
              return !!ghost;
            }"""
        )
        if framed:
            break
        page.wait_for_timeout(1000)
    print(f"  [fog] ghost framed: {framed}")
    page.wait_for_timeout(900)  # let tiles settle in the final frame


SHOTS: dict[str, dict] = {
    "hero":    {"setup": shot_hero,    "viewport": (1600, 900), "clip": None},
    "filters": {"setup": shot_filters, "viewport": (1600, 900), "clip": None},
    "symbols": {"setup": shot_symbols, "viewport": (1200, 700), "clip": None},
    # clip box stays in CSS pixels (Playwright handles the DSF multiplication).
    "hud":     {"setup": shot_hud,     "viewport": (1600, 900),
                "clip": {"x": 0, "y": 620, "width": 1600, "height": 280}},
    "bra":     {"setup": shot_bra,     "viewport": (1600, 900), "clip": None},
    "routes":  {"setup": shot_routes,  "viewport": (1600, 900), "clip": None},
    "marks":   {"setup": shot_marks,   "viewport": (1400, 800), "clip": None},
    "threats": {"setup": shot_threats, "viewport": (1600, 900), "clip": None},
    "nav":     {"setup": shot_nav,     "viewport": (1600, 900), "clip": None},
    "fog":     {"setup": shot_fog,     "viewport": (720, 540), "clip": None},
}


def capture_one(page: Page, name: str) -> None:
    spec = SHOTS[name]
    w, h = spec["viewport"]
    page.set_viewport_size({"width": w, "height": h})
    page.goto(MizMap, wait_until="domcontentloaded")
    # Wait for hydration (markers on map).
    n_markers = page.evaluate(HYDRATE_JS)
    print(f"  [{name}] markers on map: {n_markers}")
    if n_markers == 0:
        print(f"  [{name}] WARN: no markers visible — mission may not be loaded.")
        return
    spec["setup"](page)
    out = ASSETS / f"{name}.png"
    kwargs = {"path": str(out), "type": "png", "omit_background": False}
    if spec["clip"]:
        kwargs["clip"] = spec["clip"]
    page.screenshot(**kwargs)
    print(f"  [{name}] saved -> {out.relative_to(REPO_ROOT)}")


def main() -> int:
    names = sys.argv[1:] if len(sys.argv) > 1 else list(SHOTS.keys())
    unknown = [n for n in names if n not in SHOTS]
    if unknown:
        print(f"Unknown shots: {unknown}. Valid: {list(SHOTS.keys())}")
        return 1

    with sync_playwright() as p:
        # Prefer an installed system browser (no chromium download). Chrome on
        # the maintainer's box, Edge as the always-present Windows fallback,
        # then Playwright's bundled Chromium if neither channel is installed.
        browser = None
        for channel in ("chrome", "msedge"):
            try:
                browser = p.chromium.launch(channel=channel, headless=False)
                print(f"Using browser channel: {channel}")
                break
            except Exception as exc:  # noqa: BLE001
                print(f"  channel '{channel}' unavailable: {exc}")
        if browser is None:
            browser = p.chromium.launch(headless=False)  # bundled Chromium
            print("Using bundled Chromium")
        # device_scale_factor=2 captures at "Retina" density so the PNGs stay
        # sharp when viewed full-size on a high-DPI display.
        ctx = browser.new_context(
            viewport={"width": 1600, "height": 900},
            device_scale_factor=2,
        )
        ctx.add_init_script(INIT_SCRIPT)
        page = ctx.new_page()
        for name in names:
            print(f"Capturing {name} ...")
            try:
                capture_one(page, name)
            except Exception as e:
                print(f"  [{name}] FAILED: {e}")
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
