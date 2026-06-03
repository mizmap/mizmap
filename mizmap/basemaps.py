"""Selectable basemap registry for the tile proxy.

MizMap proxies *every* basemap through the local tile cache (see
`mizmap/tiles.py`) so the browser never hits an upstream tile server directly —
preserving the on-disk cache, LAN-shared warming, and rate-limit politeness for
all sources, not just the default. Each `Basemap` describes one selectable
source; `build_basemaps()` is the single source of truth consumed by both the
tile cache and `/api/config`.

The `topo` entry inherits the configured `tile_url` / `tile_attribution`, so the
existing advanced override keeps working; the others are fixed. Tile-axis order
is per-source (Esri serves `{z}/{y}/{x}`) — the cache resolves URLs by token
replacement, so order in the template is what matters.
"""

from __future__ import annotations

from dataclasses import dataclass

from mizmap.config import Settings

DEFAULT_BASEMAP_ID = "topo"


@dataclass(frozen=True)
class Basemap:
    id: str
    label: str
    upstream_url: str  # template with {z}/{x}/{y} (+ optional {s} subdomain)
    attribution: str
    max_native_zoom: int
    content_type: str  # "image/png" | "image/jpeg"
    subdomains: str  # e.g. "abc"; "" when the source has no {s}

    @property
    def ext(self) -> str:
        return "jpg" if self.content_type == "image/jpeg" else "png"


def build_basemaps(settings: Settings) -> list[Basemap]:
    """Build the basemap list. `topo` reflects the configured tile settings."""
    return [
        Basemap(
            id=DEFAULT_BASEMAP_ID,
            label="Topographic",
            upstream_url=settings.tile_url,
            attribution=settings.tile_attribution,
            max_native_zoom=17,
            content_type="image/png",
            subdomains="abc",
        ),
        Basemap(
            id="streets",
            label="Streets",
            upstream_url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attribution="© OpenStreetMap contributors",
            max_native_zoom=19,
            content_type="image/png",
            subdomains="abc",
        ),
        Basemap(
            id="sat",
            label="Satellite",
            upstream_url=(
                "https://server.arcgisonline.com/ArcGIS/rest/services/"
                "World_Imagery/MapServer/tile/{z}/{y}/{x}"
            ),
            attribution="Imagery © Esri, Maxar, Earthstar Geographics",
            max_native_zoom=19,
            content_type="image/jpeg",
            subdomains="",
        ),
    ]
