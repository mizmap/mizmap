"""Probe DCS-gRPC's GetMagneticDeclination at globally-distributed reference
points with well-established real-world declination SIGNS, to decide whether the
Afghanistan sign flip is a universal bug or region-specific.

GetMagneticDeclination is pure IGRF math at the mission date, so it should accept
any lat/lon regardless of the loaded theatre. If every point comes back with the
sign opposite to reality, the flip is universal and a blanket negation is safe.

    MIZMAP_GRPC_HOST=192.168.1.116 uv run python scripts/diag_decl_global.py
"""

from __future__ import annotations

import asyncio
import os

import grpc

import mizmap.proto_gen  # noqa: F401  -- sets sys.path for generated imports
from dcs.custom.v0 import custom_pb2, custom_pb2_grpc

# (name, lat, lon, real-world declination sign + approx magnitude). Signs are
# geographically unambiguous; the large-|value| sites make the sign read clean
# even with 2013-vs-now secular slop. Positive = easterly (real-world convention).
POINTS = [
    ("Las Vegas, NV", 36.08, -115.15, +11.5),
    ("New York, NY", 40.71, -74.01, -13.0),
    ("Sao Paulo, BR", -23.55, -46.63, -21.5),
    ("Sydney, AU", -33.87, 151.21, +12.5),
    ("Tokyo, JP", 35.68, 139.77, -7.5),
    ("Wellington, NZ", -41.29, 174.78, +22.5),
    ("Reykjavik, IS", 64.13, -21.90, -15.0),
    ("Kandahar (anchor)", 31.51, 65.85, +2.9),  # DCS F10 says +2.9 easterly here
]


async def main() -> None:
    host = os.environ.get("MIZMAP_GRPC_HOST", "127.0.0.1")
    port = int(os.environ.get("MIZMAP_GRPC_PORT", "50051"))
    async with grpc.aio.insecure_channel(f"{host}:{port}") as channel:
        await asyncio.wait_for(channel.channel_ready(), timeout=5.0)
        stub = custom_pb2_grpc.CustomServiceStub(channel)

        print(f"{'location':<20} {'real ~':>8} {'gRPC':>8}  verdict")
        print("-" * 52)
        flips = same = errors = 0
        for name, lat, lon, real in POINTS:
            try:
                resp = await asyncio.wait_for(
                    stub.GetMagneticDeclination(
                        custom_pb2.GetMagneticDeclinationRequest(lat=lat, lon=lon, alt=0.0)
                    ),
                    timeout=8.0,
                )
                grpc_val = float(resp.declination)
            except grpc.aio.AioRpcError as exc:
                print(f"{name:<20} {real:>+8.1f} {'ERR':>8}  ({exc.code().name})")
                errors += 1
                continue

            if grpc_val == 0.0:
                verdict = "zero/no-data"
            elif (grpc_val > 0) == (real > 0):
                verdict = "same sign"
                same += 1
            else:
                verdict = "FLIPPED"
                flips += 1
            print(f"{name:<20} {real:>+8.1f} {grpc_val:>+8.2f}  {verdict}")

        print("-" * 52)
        print(f"flipped={flips}  same-sign={same}  errors={errors}")
        if flips and not same:
            print("→ Sign is flipped at EVERY point: universal bug, blanket negation is safe.")
        elif same and not flips:
            print("→ gRPC matches reality everywhere: NO flip — Afghanistan needs another look.")
        elif flips and same:
            print("→ MIXED: region-dependent. A blanket negation would be WRONG.")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
