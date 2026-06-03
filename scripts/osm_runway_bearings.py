"""One-off: fetch real runway geometry from OpenStreetMap (the source OpenTopoMap
renders) and compute each runway's true bearing from its endpoint coordinates.

This is the independent ground truth for the runway-overlay diagnostic: it's the
exact base-map MizMap draws over, so DCS `course` vs this bearing is precisely
the angular offset the user sees. No designator rounding, no declination.
"""

from __future__ import annotations

import math

import httpx

# Airport reference points (lat, lon) — Kandahar OAKN, Herat OAHR, Khost OAKS.
AIRPORTS = {
    "Kandahar (OAKN)": (31.5058, 65.8480),
    "Herat (OAHR)": (34.2100, 62.2283),
    "Khost (OAKS)": (33.3334, 69.9520),
}

OVERPASS = "https://overpass-api.de/api/interpreter"


def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial true bearing (degrees, 0..360) from point 1 to point 2."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return math.degrees(math.atan2(y, x)) % 360.0


def main() -> None:
    parts = []
    for lat, lon in AIRPORTS.values():
        parts.append(f'way["aeroway"="runway"](around:3500,{lat},{lon});')
    query = f"[out:json][timeout:30];({''.join(parts)});out geom;"

    resp = httpx.post(
        OVERPASS,
        data={"data": query},
        headers={"User-Agent": "mizmap-runway-diag/1.0"},
        timeout=60.0,
    )
    resp.raise_for_status()
    elements = resp.json().get("elements", [])

    print(f"OSM returned {len(elements)} runway way(s)\n")
    for name, (alat, alon) in AIRPORTS.items():
        print(f"=== {name} ===")
        near = [
            el
            for el in elements
            if el.get("geometry")
            and _close(el["geometry"][0], alat, alon, 0.06)
        ]
        if not near:
            print("  (no runway way found near this airport)\n")
            continue
        for el in near:
            geom = el["geometry"]
            la1, lo1 = geom[0]["lat"], geom[0]["lon"]
            la2, lo2 = geom[-1]["lat"], geom[-1]["lon"]
            brg = bearing(la1, lo1, la2, lo2)
            ref = el.get("tags", {}).get("ref", "?")
            print(
                f"  ref={ref:<7} true bearing (end→end) = {brg:6.1f}°  "
                f"(reciprocal {(brg + 180) % 360:6.1f}°)  nodes={len(geom)}"
            )
        print()


def _close(node: dict, lat: float, lon: float, tol_deg: float) -> bool:
    return abs(node["lat"] - lat) < tol_deg and abs(node["lon"] - lon) < tol_deg


if __name__ == "__main__":
    main()
