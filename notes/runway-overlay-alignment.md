# Runway overlay alignment (DCS vs. real-world base maps)

*Engineering note. Validated against a live Afghanistan mission (DCS-gRPC 0.8.1,
mission dated 2013-02-02) in June 2026.*

## TL;DR

The DCS-sourced **runway overlay** can appear rotated by a few degrees relative
to the runway drawn on the OpenTopoMap / OpenStreetMap base layer, while the
runway **center stays aligned**. This is **not a MizMap bug**. It is the
difference between two independent representations of the same runway — DCS's
terrain model and OpenStreetMap's trace — each carrying a degree or two of
per-feature orientation error. MizMap faithfully draws DCS's geometry; that is
the correct thing to draw, because in the sim you land where DCS put the runway,
not where OSM drew it. **No runway code change is warranted.**

## The observation

Zooming into an airfield, the grey runway overlay (from DCS) and the runway on
the topo base map share a center but diverge in angle — the overlay line splays
off the base-map strip toward the ends, by more than half the runway width at
the tips. Position looks correct; only orientation is off.

## Why a rotation with no position shift? (the geodesy)

A natural worry: if the divergence came from a projection / CRS mismatch, you'd
expect a **shift** (and scale) as well as a rotation — they couple. The fact
that we see rotation *without* a coupled shift is itself evidence that the cause
is **not** a projection mismatch. Here's why there isn't one:

- **Position and orientation travel through different transforms.** The runway
  *center* comes from `coord.LOtoLL(rw.position)` — DCS runs the full inverse of
  its own theatre projection and hands us WGS84 lat/lon. We render in Web
  Mercator, the **same CRS** OpenTopoMap/OSM use. We never reproject DCS
  coordinates with a *different* CRS, so position is correct by construction.
  The *orientation* is the raw `getRunways().course` heading (sign-corrected);
  it never passes through the position transform.
- Because the two are computed independently, an error in one does not imply an
  error in the other. A CRS mismatch would corrupt the *position* transform for
  everything (a global shift+rotation growing with distance from a reference) —
  but there is no such mismatch to corrupt.
- The few-degree angle is a **per-feature** modeling/digitization difference:
  DCS's artists model each runway, OSM's mappers trace each runway, and each
  lands the *orientation* a degree or two off the real strip, independently per
  airfield. Rotating a feature about its own center changes its angle but not
  its center → exactly "position right, angle wrong."
- The fingerprint confirms per-feature noise rather than a global transform: the
  offsets are **mixed-sign and varying magnitude** across fields. A projection
  error would be smooth and consistent across neighbours.

We also explicitly ruled out **grid convergence** (DCS grid-north vs. true-north),
the one projection-flavoured candidate: the measured convergence sweeps several
degrees across Afghanistan, but the runway error does not track it and applying
it makes the fit *worse* — so DCS's `course` is already true-referenced. (And
even convergence would, in this pipeline, produce rotation without a shift,
because position goes through the correct `LOtoLL` while a grid-frame heading
drawn as true would simply be rotated.)

## Why a "small" angle is plainly visible: the lever arm

A few-degrees angular agreement is *not* a few-meters overlay agreement on a
long feature. Over a ~1.5 km half-length, a 1.6° tilt becomes tens of meters of
lateral displacement at the runway ends — enough to walk the line off the strip.

Measured against OSM geometry (the exact source OpenTopoMap renders), using
full-precision DCS centers/courses/lengths pulled live via Eval:

| field | drawn °T | OSM °T | dθ | end offset | half-width | center offset |
|---|--:|--:|--:|--:|--:|--:|
| Kandahar 23 | 233.7 | 235.3 | −1.6° | **41 m** | 30 m | **12 m** |
| Herat 18 | 187.7 | 187.5 | +0.2° | 4 m | 30 m | 19 m |
| Khost 23 | 237.8 | 241.4 | −3.6° | 53 m | 22 m | 148 m |

`end offset = ½ · DCS-length · sin(dθ)` — DCS's own runway length, since that is
the line MizMap actually draws. OSM bearing is a least-squares principal-axis fit
over all runway nodes (robust to displaced thresholds and 2-node ways).

- **Kandahar** is the clean exemplar: center **12 m** off (correct — a third of
  the runway's own width), but the 1.6° tilt becomes **41 m** at the ends, beyond
  the 30 m half-width. Position is right; the visible miss is *entirely* angular
  amplification. Position error (~12 m) and angular splay (~41 m) are decoupled
  and differ by nearly 4×.
- **Herat** is the control: 0.2° → 4 m, so the line overlays the strip — and it
  looks glued on.

Runways are the **only DCS *linear* ground feature** we overlay on a real-world
twin. Point features (airbase symbols, units, navaids) have no orientation to
diverge, so they only ever show the (negligible) position error — which is why
the tilt has nowhere else to show up.

## Which side is "more wrong" — DCS or OSM?

It varies by field. Triangulating each drawn line against the designator-implied
"charted" true heading (`runway number × 10 + magnetic declination`):

- **Kandahar** — the drawn DCS line (233.7°) is *closer* to charted (232.9°) than
  OSM (235.3°). Here the visible gap is mostly **OSM's digitization**, not DCS.
- **Herat** — DCS and OSM agree (≈ the strip); aligned.
- **Khost** — **DCS** carries the gap (237.8° vs. OSM 241.4° / charted 242.5°),
  and DCS even labels it "23" where the real field is **06/24**.

So neither source is systematically the culprit — this is two *independent*
representations each with a degree or two of per-feature error, with reality
somewhere between them.

## Caveats

- **DCS dimensions differ from real**, too: Kandahar is **2981 m × 60 m** in DCS
  vs. 3210 × 45 real. A separate per-feature modeling difference, independent of
  the angle.
- **Khost's 148 m center offset is partly apples-to-oranges** — DCS models/labels
  a "23" strip while the real field (OAKS) has runways 06/24 and 09/27, so the
  matched OSM way may not be the same physical strip.
- **OSM has its own digitization noise** (displaced thresholds, sparse 2-node
  ways). The principal-axis fit mitigates it but doesn't eliminate it; treat OSM
  as a good-but-imperfect "truth," not ground truth.
- Measurements were taken under DCS **active pause** — Eval still services static
  world queries there. A **full** pause stalls every Eval RPC (see CLAUDE.md).

## Decisions

- **No runway code change.** The overlay correctly follows DCS geometry, which is
  the truth for navigation (you land where DCS put the runway). "Correcting" the
  overlay to match the base map would point it a few degrees off from the actual
  touchdown line. The base-map mismatch is cosmetic and unavoidable: no
  real-world base aligns to DCS (they all share the same DCS-vs-reality gap), and
  DCS's own map is not available as a consumable tile source.
- **Basemap selector** (Topographic / Streets / Satellite) was added as a UX
  feature around this time. It does **not** address the tilt — every real-world
  base carries the same gap — and was never expected to.
- **Related bug found during this investigation:** DCS-gRPC 0.8.1 returns
  magnetic declination with the sign inverted. That *was* a real, fixable bug
  (the telemetry HUD and BRA tool read ~5° off the cockpit) and is fixed —
  see [`proto/UPSTREAM.md`](../proto/UPSTREAM.md) and `mizmap/grpc_client.py`.

## Reproducing it

The probe scripts in [`scripts/`](../scripts/), run against a live mission with
`MIZMAP_GRPC_HOST=<dcs-box>` (Eval-gated work needs `evalEnabled = true`):

- `diag_runways.py` — per-runway drawn-vs-designator heading and in-engine grid
  convergence; rules convergence (and magnetic) out as the cause.
- `osm_runway_bearings.py` — real runway true bearings from OSM via Overpass (the
  base-map "truth").
- `diag_runway_centers.py` — full-precision DCS runway centers/course/length/width
  via the runways Eval (works under active pause).
- `diag_runway_offset.py` — combines the above into the dθ / end-offset /
  center-offset table above.

(`diag_decl_global.py` and `diag_missiondate.py` belong to the related
declination-sign investigation.)
