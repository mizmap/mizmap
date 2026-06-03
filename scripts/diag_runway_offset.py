"""Quantify the runway-overlay offset, to reconcile "small angle" with "visible
miss at the ends".

For three Afghanistan fields it fetches the real runway geometry from OSM (what
OpenTopoMap renders), computes its true bearing (first→last node AND a
least-squares principal axis, robust to displaced thresholds), length, and
midpoint, then combines with DCS's drawn course + center to report:

  - dθ       : angular difference between the drawn line and the OSM strip
  - end_off  : lateral offset at each runway END = (length/2)·sin(dθ)   <-- the eye sees this
  - half_w   : half the runway width (the strip's own edge)
  - ctr_off  : center-to-center distance (DCS coord.LOtoLL center vs OSM midpoint)
  - exp_T    : designator-implied true heading (desig_mag + declination)

DCS centers carry only the 3-decimal precision of the earlier diagnostic
(~100 m), so ctr_off is an upper-ish estimate; dθ/end_off are exact.
"""

from __future__ import annotations

import math

import httpx

# DCS-side values from the live Afghanistan run (scripts/diag_runways.py) + the
# F10 declination. width_m / length hints from OurAirports where DCS length isn't
# to hand; the script prefers the OSM-measured length for end_off.
DCS = {
    "Kandahar 23": {"course": 233.72, "lat": 31.505774, "lon": 65.847656, "desig_mag": 230, "decl": 2.9, "len": 2980.9, "width": 60},
    "Herat 18": {"course": 187.70, "lat": 34.207906, "lon": 62.227941, "desig_mag": 180, "decl": 3.3, "len": 2718.8, "width": 60},
    "Khost 23": {"course": 237.85, "lat": 33.333062, "lon": 69.950993, "desig_mag": 240, "decl": 2.5, "len": 1712.7, "width": 45},
}
REF = {
    "Kandahar 23": (31.5058, 65.8480),
    "Herat 18": (34.2100, 62.2283),
    "Khost 23": (33.3334, 69.9520),
}

OVERPASS = "https://overpass-api.de/api/interpreter"
_R = 6371000.0


def _haversine(la1, lo1, la2, lo2):
    p1, p2 = math.radians(la1), math.radians(la2)
    dp = math.radians(la2 - la1)
    dl = math.radians(lo2 - lo1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * _R * math.asin(math.sqrt(a))


def _principal_bearing(geom, lat0, lon0):
    clat = math.cos(math.radians(lat0))
    e = [(p["lon"] - lon0) * clat * 111320.0 for p in geom]
    n = [(p["lat"] - lat0) * 110540.0 for p in geom]
    me, mn = sum(e) / len(e), sum(n) / len(n)
    sxx = sum((x - me) ** 2 for x in e)
    syy = sum((y - mn) ** 2 for y in n)
    sxy = sum((x - me) * (y - mn) for x, y in zip(e, n))
    phi = 0.5 * math.atan2(2 * sxy, sxx - syy)  # major-axis angle from east (math CCW)
    return math.degrees(math.atan2(math.cos(phi), math.sin(phi))) % 360.0


def _signed_mod180(deg):
    d = deg % 180.0
    return d - 180.0 if d > 90.0 else d


def main():
    parts = [f'way["aeroway"="runway"](around:3500,{la},{lo});' for la, lo in REF.values()]
    query = f"[out:json][timeout:30];({''.join(parts)});out geom;"
    resp = httpx.post(OVERPASS, data={"data": query},
                      headers={"User-Agent": "mizmap-runway-offset/1.0"}, timeout=60.0)
    resp.raise_for_status()
    ways = [el for el in resp.json().get("elements", []) if el.get("geometry")]

    print(f"{'field':<13}{'drawnT':>8}{'osmT':>8}{'expT':>8}{'dθ':>7}{'end_off':>9}{'half_w':>8}{'ctr_off':>9}")
    print("-" * 78)
    for name, (rlat, rlon) in REF.items():
        d = DCS[name]
        near = [w for w in ways if _haversine(w["geometry"][0]["lat"], w["geometry"][0]["lon"], rlat, rlon) < 7000]
        if not near:
            print(f"{name:<13} (no OSM runway found)")
            continue
        # Longest way = the main runway (avoid short displaced/stopway segments).
        def _len(w):
            g = w["geometry"]
            return _haversine(g[0]["lat"], g[0]["lon"], g[-1]["lat"], g[-1]["lon"])
        w = max(near, key=_len)
        g = w["geometry"]
        osm_brg = _principal_bearing(g, rlat, rlon)
        mid_lat = (g[0]["lat"] + g[-1]["lat"]) / 2
        mid_lon = (g[0]["lon"] + g[-1]["lon"]) / 2

        dtheta = _signed_mod180(d["course"] - osm_brg)
        # End offset uses DCS's own length — that's the line MizMap actually draws.
        end_off = (d["len"] / 2) * math.sin(math.radians(abs(dtheta)))
        ctr_off = _haversine(d["lat"], d["lon"], mid_lat, mid_lon)
        exp_t = (d["desig_mag"] + d["decl"]) % 360.0

        print(f"{name:<13}{d['course']:>8.1f}{osm_brg % 360:>8.1f}{exp_t:>8.1f}"
              f"{dtheta:>7.1f}{end_off:>8.0f}m{d['width'] / 2:>7.0f}m{ctr_off:>8.0f}m")


if __name__ == "__main__":
    main()
