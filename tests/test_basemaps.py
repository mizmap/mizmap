"""Unit tests for the basemap registry and the multi-source tile cache."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from mizmap.basemaps import DEFAULT_BASEMAP_ID, Basemap, build_basemaps
from mizmap.tiles import TileCache


def _settings(tile_url: str, attr: str) -> SimpleNamespace:
    # build_basemaps only reads tile_url/tile_attribution off settings.
    return SimpleNamespace(tile_url=tile_url, tile_attribution=attr)


def test_build_basemaps_topo_reflects_settings():
    maps = build_basemaps(_settings("https://custom/{z}/{x}/{y}.png", "© Custom"))
    by_id = {b.id: b for b in maps}
    assert DEFAULT_BASEMAP_ID == "topo"
    # The default (topo) inherits the configured upstream + attribution.
    assert by_id["topo"].upstream_url == "https://custom/{z}/{x}/{y}.png"
    assert by_id["topo"].attribution == "© Custom"
    # The fixed alternates are always present.
    assert {"streets", "sat"} <= set(by_id)


def test_basemap_ext_by_content_type():
    png = Basemap("a", "A", "u", "x", 17, "image/png", "abc")
    jpg = Basemap("b", "B", "u", "x", 19, "image/jpeg", "")
    assert png.ext == "png"
    assert jpg.ext == "jpg"


def _cache(tmp_path: Path) -> TileCache:
    maps = [
        Basemap("topo", "Topo", "https://t/{s}/{z}/{x}/{y}.png", "©", 17, "image/png", "abc"),
        Basemap("sat", "Sat", "https://e/tile/{z}/{y}/{x}", "©", 19, "image/jpeg", ""),
    ]
    return TileCache(basemaps=maps, cache_dir=tmp_path)


def test_has_source_and_content_type(tmp_path):
    tc = _cache(tmp_path)
    assert tc.has_source("topo")
    assert tc.has_source("sat")
    assert not tc.has_source("bogus")
    assert tc.content_type("topo") == "image/png"
    assert tc.content_type("sat") == "image/jpeg"


def test_tile_path_is_source_scoped_with_ext(tmp_path):
    tc = _cache(tmp_path)
    assert tc._tile_path("topo", 5, 10, 12) == tmp_path / "topo" / "5" / "10" / "12.png"
    assert tc._tile_path("sat", 5, 10, 12) == tmp_path / "sat" / "5" / "10" / "12.jpg"


def test_upstream_url_respects_per_source_axis_order(tmp_path):
    tc = _cache(tmp_path)
    # {s} → first subdomain; standard {z}/{x}/{y}.
    assert tc._upstream_url("topo", 5, 10, 12) == "https://t/a/5/10/12.png"
    # Esri serves {z}/{y}/{x} — y and x must land in the right slots.
    assert tc._upstream_url("sat", 5, 10, 12) == "https://e/tile/5/12/10"
