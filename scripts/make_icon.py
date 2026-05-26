"""Generate mizmap/data/mizmap.ico — a multi-resolution compass-rose icon.

Run once when you want to refresh the icon:

    uv run python scripts/make_icon.py

The output is committed to the repo so end users + the build don't need
PIL installed at runtime just to load the icon. Sizes 16/32/48/256 cover
the Windows Explorer + tray + alt-tab + Start menu use cases.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw


# Canvas + colour palette. Drawn at high res; PIL downsamples to each
# size baked into the .ico.
CANVAS = 256
BG = (14, 42, 71)             # deep navy
RING = (166, 192, 224)        # pale steel
SPOKE_MAJOR = (240, 244, 252) # near-white for cardinals
SPOKE_MINOR = (170, 195, 225) # softer for ordinals
NORTH = (231, 76, 60)         # warm red for the N spoke
HUB = (240, 244, 252)


def _spoke(draw: ImageDraw.ImageDraw, cx: float, cy: float, angle_rad: float,
           length: float, half_width: float, fill: tuple) -> None:
    """Draw a single tapered spoke pointing along `angle_rad` (0 = north, CW)."""
    # Outward tip.
    tip = (cx + length * math.sin(angle_rad), cy - length * math.cos(angle_rad))
    # Base corners — perpendicular to the spoke direction.
    left = (
        cx + half_width * math.sin(angle_rad - math.pi / 2),
        cy - half_width * math.cos(angle_rad - math.pi / 2),
    )
    right = (
        cx + half_width * math.sin(angle_rad + math.pi / 2),
        cy - half_width * math.cos(angle_rad + math.pi / 2),
    )
    draw.polygon([tip, left, right], fill=fill)


def render(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size / 2

    # Disc + ring.
    pad = max(2, size // 32)
    draw.ellipse((pad, pad, size - pad, size - pad), fill=BG)
    ring_pad = pad + max(2, size // 32)
    draw.ellipse(
        (ring_pad, ring_pad, size - ring_pad, size - ring_pad),
        outline=RING,
        width=max(1, size // 64),
    )

    # Spoke geometry. Cardinals reach further than ordinals; the N spoke is
    # accent-coloured.
    cardinal_len = (size / 2 - ring_pad - size / 32) * 0.96
    ordinal_len = cardinal_len * 0.55
    cardinal_w = max(1.0, size / 28)
    ordinal_w = max(1.0, size / 40)

    # Ordinals first, so they sit under the cardinals at the hub.
    for angle_deg in (45, 135, 225, 315):
        _spoke(draw, cx, cy, math.radians(angle_deg), ordinal_len, ordinal_w, SPOKE_MINOR)

    # Cardinals.
    for angle_deg in (90, 180, 270):
        _spoke(draw, cx, cy, math.radians(angle_deg), cardinal_len, cardinal_w, SPOKE_MAJOR)
    # North gets the accent.
    _spoke(draw, cx, cy, math.radians(0), cardinal_len, cardinal_w, NORTH)

    # Hub.
    hub_r = max(2, size // 18)
    draw.ellipse((cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r), fill=HUB)

    return img


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "mizmap" / "data" / "mizmap.ico"
    # Render at the largest size, then let PIL downsample for the smaller
    # variants packed into the multi-res .ico.
    master = render(256)
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    master.save(out, format="ICO", sizes=sizes)
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
