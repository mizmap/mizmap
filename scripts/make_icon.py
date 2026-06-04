"""Generate the MizMap brand mark — a flight-plan "route trail" icon.

The mark is a cased route polyline tracing an "M" (the MizMap initial) over
five waypoint nodes, set in a navy disc with a pale steel ring. The bottom-left
node is accent-red (the route start); the rest are white. It reads as a mission
flight plan, mirrors how MizMap draws routes on the live map, and is distinct
from any compass-rose / navigation-star mark.

Run when you want to refresh the icon (Pillow is a build-time-only dep):

    uv run --with pillow python scripts/make_icon.py

It writes all three committed brand assets from this single source:

  * mizmap/data/mizmap.ico        — app window, tray, Windows installer
  * docs/favicon.ico              — landing-page favicon (byte copy of the .ico)
  * docs/assets/mizmap-icon.png   — landing-page brand glyph + apple-touch-icon

The outputs are committed so end users + the build don't need PIL at runtime.
ICO sizes 16/32/48/64/128/256 cover Explorer + tray + alt-tab + Start menu;
each is rendered natively (not downscaled from one master) so small sizes keep
crisp strokes.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw


# Colour palette — reuses MizMap's existing identity.
BG = (14, 42, 71)         # deep navy disc
RING = (166, 192, 224)    # pale steel ring
CASE = (7, 22, 40)        # dark casing under the route line
LINE = (240, 244, 252)    # near-white route line + waypoint nodes
NODE_EDGE = (7, 22, 40)   # node outline
START = (231, 76, 60)     # accent red — the route start node

# Render this many times larger, then downsample, for clean anti-aliased edges.
SUPERSAMPLE = 4

# Waypoint nodes tracing an "M", normalised to the disc (x, y in [0, 1], y down).
# First node is the route start (drawn red); the polyline is the flight plan.
ROUTE = [
    (0.29, 0.71),  # start  (bottom-left)
    (0.29, 0.31),  # left peak
    (0.50, 0.56),  # centre valley
    (0.71, 0.31),  # right peak
    (0.71, 0.71),  # end    (bottom-right)
]


def render(size: int) -> Image.Image:
    """Render the mark at `size`x`size` px (RGBA), supersampled for clean edges."""
    s = size * SUPERSAMPLE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Disc + ring.
    pad = max(2, s // 32)
    draw.ellipse((pad, pad, s - pad, s - pad), fill=BG)
    ring_pad = pad + max(2, s // 32)
    draw.ellipse(
        (ring_pad, ring_pad, s - ring_pad, s - ring_pad),
        outline=RING,
        width=max(1, s // 48),
    )

    pts = [(x * s, y * s) for (x, y) in ROUTE]

    # Cased route line: a dark halo under the bright line, as on the live map.
    line_w = max(2 * SUPERSAMPLE, int(s * 0.052))
    case_w = line_w + max(2 * SUPERSAMPLE, int(s * 0.045))
    draw.line(pts, fill=CASE, width=case_w, joint="curve")
    draw.line(pts, fill=LINE, width=line_w, joint="curve")

    # Waypoint nodes. Middles + end are white; the start is accent-red.
    node_r = max(3 * SUPERSAMPLE, int(s * 0.060))
    edge_w = max(1, SUPERSAMPLE)

    def node(center: tuple, radius: float, fill: tuple) -> None:
        x, y = center
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=fill,
            outline=NODE_EDGE,
            width=edge_w,
        )

    for c in pts[1:]:
        node(c, node_r, LINE)
    node(pts[0], node_r * 1.05, START)

    return img.resize((size, size), Image.Resampling.LANCZOS)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    ico_path = root / "mizmap" / "data" / "mizmap.ico"
    favicon_path = root / "docs" / "favicon.ico"
    png_path = root / "docs" / "assets" / "mizmap-icon.png"

    sizes = [16, 32, 48, 64, 128, 256]
    images = [render(s) for s in sizes]
    # Pack the natively-rendered per-size bitmaps into one multi-res ICO. The
    # base image must be the largest — the ICO writer drops any requested size
    # bigger than the base, so saving from a small frame would yield only it.
    largest = images[-1]
    largest.save(
        ico_path,
        format="ICO",
        append_images=images[:-1],
        sizes=[(s, s) for s in sizes],
    )
    shutil.copyfile(ico_path, favicon_path)
    images[-1].save(png_path, format="PNG")

    for p in (ico_path, favicon_path, png_path):
        print(f"wrote {p} ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
