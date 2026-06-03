"""Diagnostic: is the runway-overlay angular offset grid convergence or magnetic?

Standalone — talks straight to a DCS-gRPC server (no `mizmap serve` needed),
walks every airbase runway, and for each one compares the bearing MizMap
currently *draws* against the runway's designator-implied true bearing, plus the
DCS grid-north-vs-true-north convergence measured in-engine at that point.

Why this isolates the cause:
  - Runway *position* is fully georeferenced (`coord.LOtoLL`), so centers are
    correct. Only the *heading* (`getRunways().course`) is suspect, and the only
    question is which frame it lives in.
  - We probe convergence directly: step ~1 km true-north (lat + dlat) from each
    runway and read the point back in DCS world XY via `coord.LLtoLO`. The east
    component of that "pure north" step is the grid convergence angle at that
    point — no map-projection parameters required.

Reading the table (rows sorted by longitude):
  - tNow  = how far our drawn bearing sits from the designator-implied truth.
  - conv  = DCS grid-north relative to true-north here (grid→true rotation).
  - tCorr = the same residual after rotating the drawn bearing by +conv.
  If tNow tracks -conv, flips sign across the map's central meridian, and tCorr
  collapses toward 0 → it's GRID CONVERGENCE (and the fix is course + conv).
  If tNow is ~constant theatre-wide and tracks -decl → it's a MAGNETIC mislabel.

Run against the LAN DCS box:
    MIZMAP_GRPC_HOST=192.168.1.116 uv run python scripts/diag_runways.py

Requires `evalEnabled = true` in dcs-grpc.lua (the convergence probe uses Eval).
"""

from __future__ import annotations

import asyncio
import json
import math
import os

import grpc

import mizmap.proto_gen  # noqa: F401  -- sets sys.path for generated imports
from dcs.custom.v0 import custom_pb2, custom_pb2_grpc
from dcs.world.v0 import world_pb2, world_pb2_grpc

# Walk every runway; alongside its georeferenced center, return the DCS world-XY
# delta of a small true-north step so the caller can recover the convergence
# angle. (+x = grid north, +z = grid east, per the DCS coordinate convention.)
PROBE_LUA = r"""
local out = {}
if not world or not world.getAirbases then return out end
local dlat = 0.01
for _, ab in pairs(world.getAirbases()) do
  local rws = ab:getRunways()
  if rws then
    for _, rw in ipairs(rws) do
      if rw.position then
        local lat, lon = coord.LOtoLL(rw.position)
        local p0 = coord.LLtoLO(lat, lon, 0)
        local pn = coord.LLtoLO(lat + dlat, lon, 0)
        out[#out + 1] = {
          airbase_name = ab:getName(),
          name = rw.Name,
          course = rw.course or 0,
          lat = lat,
          lon = lon,
          dnorth = pn.x - p0.x,
          deast = pn.z - p0.z,
        }
      end
    end
  end
end
return out
"""

_TWO_PI = 2.0 * math.pi


def _norm360(deg: float) -> float:
    return deg % 360.0


def _signed180(deg: float) -> float:
    """Wrap to (-180, 180]."""
    d = (deg + 180.0) % 360.0 - 180.0
    return d + 360.0 if d <= -180.0 else d


def _signed_mod180(deg: float) -> float:
    """Wrap an undirected-line angle difference to (-90, 90].

    A runway is a line, not an arrow: comparing `course` to its designator must
    ignore the 180° reciprocal so only the real tilt shows.
    """
    d = deg % 180.0
    return d - 180.0 if d > 90.0 else d


def _designator_mag(name: object) -> float | None:
    """Designator (e.g. 33) → implied magnetic heading (330°), or None.

    Bounded to 1..36: ships (carriers/LHAs) report deck "runways" with junk
    designators (480, -2133236846, 0) that would otherwise contaminate the stats.
    """
    try:
        n = int(round(float(name)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not 1 <= n <= 36:
        return None
    return _norm360(n * 10.0)


def _stdev(xs: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mean = sum(xs) / n
    return math.sqrt(sum((x - mean) ** 2 for x in xs) / n)


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0.0 or sy == 0.0:
        return 0.0
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return cov / (sx * sy)


async def main() -> int:
    host = os.environ.get("MIZMAP_GRPC_HOST", "127.0.0.1")
    port = int(os.environ.get("MIZMAP_GRPC_PORT", "50051"))
    target = f"{host}:{port}"
    print(f"Connecting to DCS-gRPC at {target} ...")

    async with grpc.aio.insecure_channel(target) as channel:
        try:
            await asyncio.wait_for(channel.channel_ready(), timeout=5.0)
        except asyncio.TimeoutError:
            print(f"  ! could not connect to {target} (is DCS-gRPC bound to the LAN?)")
            return 1

        world_stub = world_pb2_grpc.WorldServiceStub(channel)
        custom_stub = custom_pb2_grpc.CustomServiceStub(channel)

        try:
            theatre_resp = await asyncio.wait_for(
                world_stub.GetTheatre(world_pb2.GetTheatreRequest()), timeout=5.0
            )
            theatre = theatre_resp.theatre or "?"
        except grpc.aio.AioRpcError as exc:
            theatre = f"? ({exc.code().name})"

        try:
            eval_resp = await asyncio.wait_for(
                custom_stub.Eval(custom_pb2.EvalRequest(lua=PROBE_LUA)), timeout=20.0
            )
        except grpc.aio.AioRpcError as exc:
            print(f"  ! runway probe Eval failed: {exc.code().name} — {exc.details()}")
            if exc.code() == grpc.StatusCode.FAILED_PRECONDITION:
                print("    → set evalEnabled = true in dcs-grpc.lua and restart DCS.")
            return 1

        try:
            rows = json.loads(eval_resp.json)
        except json.JSONDecodeError:
            print(f"  ! probe returned non-JSON: {eval_resp.json[:200]!r}")
            return 1
        if not isinstance(rows, list) or not rows:
            print(f"  ! probe returned no runways (theatre={theatre}).")
            return 1

        # Magnetic declination per runway — a plain RPC (no Eval), fired together.
        decls = await asyncio.gather(
            *(
                _fetch_declination(custom_stub, r.get("lat", 0.0), r.get("lon", 0.0))
                for r in rows
            )
        )

    records = []
    for r, decl in zip(rows, decls):
        lat = float(r.get("lat", 0.0))
        lon = float(r.get("lon", 0.0))
        # Drawn bearing: the production pipeline negates the raw course.
        course_t = _norm360(math.degrees((-float(r.get("course", 0.0))) % _TWO_PI))
        # Convergence: bearing of true-north as seen in the grid frame is
        # atan2(deast, dnorth); the grid→true correction is its negation.
        beta = math.degrees(math.atan2(float(r.get("deast", 0.0)), float(r.get("dnorth", 0.0))))
        conv = _signed180(-beta)

        mag = _designator_mag(r.get("name"))
        if decl is None or mag is None:
            desig_t = None
            t_now = t_corr = None
        else:
            desig_t = _norm360(mag + decl)
            t_now = _signed_mod180(course_t - desig_t)
            t_corr = _signed_mod180(course_t + conv - desig_t)

        records.append(
            {
                "ab": str(r.get("airbase_name", "")),
                "rwy": r.get("name"),
                "lat": lat,
                "lon": lon,
                "course_t": course_t,
                "decl": decl,
                "conv": conv,
                "desig_t": desig_t,
                "t_now": t_now,
                "t_corr": t_corr,
            }
        )

    comparable = [r for r in records if r["desig_t"] is not None]
    skipped = len(records) - len(comparable)
    comparable.sort(key=lambda d: d["lon"])
    _print_table(theatre, comparable, skipped)
    return 0


async def _fetch_declination(
    stub: custom_pb2_grpc.CustomServiceStub, lat: float, lon: float
) -> float | None:
    try:
        resp = await asyncio.wait_for(
            stub.GetMagneticDeclination(
                custom_pb2.GetMagneticDeclinationRequest(lat=lat, lon=lon, alt=0.0)
            ),
            timeout=5.0,
        )
    except grpc.aio.AioRpcError:
        return None
    return float(resp.declination)


def _fmt(v: float | None, width: int = 7, prec: int = 1) -> str:
    return f"{v:>{width}.{prec}f}" if isinstance(v, (int, float)) else f"{'—':>{width}}"


def _print_table(theatre: str, records: list[dict], skipped: int = 0) -> None:
    print()
    note = f"   (+{skipped} ship/non-numbered skipped)" if skipped else ""
    print(f"Theatre: {theatre}   runways: {len(records)}{note}   (sorted W→E by longitude)")
    print(
        f"{'airbase':<20} {'rwy':>4} {'lon':>8} {'lat':>7} "
        f"{'courseT':>8} {'desigT':>7} {'decl':>6} {'conv':>6} {'tNow':>6} {'tCorr':>6}"
    )
    print("-" * 96)
    for d in records:
        rwy = d["rwy"]
        rwy_s = f"{rwy}" if rwy is not None else "—"
        print(
            f"{d['ab'][:20]:<20} {rwy_s:>4} {d['lon']:>8.3f} {d['lat']:>7.3f} "
            f"{_fmt(d['course_t'], 8)} {_fmt(d['desig_t'])} {_fmt(d['decl'], 6)} "
            f"{_fmt(d['conv'], 6)} {_fmt(d['t_now'], 6)} {_fmt(d['t_corr'], 6)}"
        )

    have = [d for d in records if d["t_now"] is not None]
    if not have:
        print("\n(no comparable designators — can't summarize)")
        return

    def _mean_abs(key: str) -> float:
        return sum(abs(d[key]) for d in have) / len(have)

    mean_now = _mean_abs("t_now")
    mean_corr = _mean_abs("t_corr")
    mean_conv = sum(abs(d["conv"]) for d in have) / len(have)
    # If conv has the wrong sign, course - conv would do better than course + conv.
    mean_corr_minus = sum(
        abs(_signed_mod180(d["course_t"] - d["conv"] - d["desig_t"])) for d in have
    ) / len(have)
    mean_decl = sum(abs(d["decl"]) for d in have) / len(have)

    # Correlate the residual against each hypothesis's prediction. Convergence
    # predicts tNow ≈ -conv; a magnetic mislabel predicts tNow ≈ -decl. Designator
    # rounding adds ±5° noise per row, so a correlation across many fields cuts
    # through it where a single airfield can't.
    ys = [d["t_now"] for d in have]
    r_conv = _pearson([-d["conv"] for d in have], ys)
    r_decl = _pearson([-d["decl"] for d in have], ys)
    conv_spread = _stdev([d["conv"] for d in have])

    print("-" * 96)
    print(f"mean |tNow|            = {mean_now:6.2f}°   (current error vs designator-true)")
    print(f"mean |tCorr| (+conv)   = {mean_corr:6.2f}°   (after grid→true correction)")
    print(f"mean |tCorr| (-conv)   = {mean_corr_minus:6.2f}°   (correction with opposite sign)")
    print(f"mean |conv|            = {mean_conv:6.2f}°   (grid convergence magnitude)")
    print(f"mean |decl|            = {mean_decl:6.2f}°   (magnetic declination magnitude)")
    print(f"conv spread (stdev)    = {conv_spread:6.2f}°   (how much convergence varies here)")
    print(f"corr(tNow, -conv)      = {r_conv:6.2f}    (→ +1 if convergence explains it)")
    print(f"corr(tNow, -decl)      = {r_decl:6.2f}    (→ +1 if magnetic explains it)")
    print()
    best = min(mean_corr, mean_corr_minus)
    if conv_spread < 0.3:
        print(
            "→ This theatre is too compact (longitude) for convergence to vary — it "
            "can't be tested here.\n  Load a wide theatre (Afghanistan) and re-run; "
            f"the residual here is small ({mean_now:.1f}°) and within designator-rounding noise."
        )
    elif best < mean_now * 0.6 and r_conv > 0.6:
        sign = "+conv" if mean_corr <= mean_corr_minus else "-conv"
        print(
            f"→ Convergence correction ({sign}) collapses the error and tracks it strongly: "
            f"the offset is GRID-NORTH vs TRUE-NORTH, not magnetic."
        )
    elif r_decl > 0.6 and abs(r_conv) < 0.4:
        print("→ Residual tracks magnetic declination, not convergence: MAGNETIC mislabel.")
    else:
        print("→ Inconclusive — inspect the per-row tNow/conv pattern vs longitude by hand.")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
