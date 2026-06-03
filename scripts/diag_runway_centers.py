"""Dump full-precision DCS runway centers (coord.LOtoLL) + course/length/width
for the three reconciliation fields, via the live runways Eval. Works under DCS
active pause (Eval still services static world queries).

    MIZMAP_GRPC_HOST=192.168.1.116 uv run python scripts/diag_runway_centers.py
"""

from __future__ import annotations

import asyncio
import math
import os

import grpc

import mizmap.proto_gen  # noqa: F401  -- sets sys.path for generated imports
from dcs.custom.v0 import custom_pb2, custom_pb2_grpc
from mizmap.runways import RUNWAYS_LUA_SNIPPET, parse_runways_json

WANT = {"Kandahar", "Herat", "Khost"}


async def main() -> None:
    host = os.environ.get("MIZMAP_GRPC_HOST", "127.0.0.1")
    port = int(os.environ.get("MIZMAP_GRPC_PORT", "50051"))
    async with grpc.aio.insecure_channel(f"{host}:{port}") as channel:
        await asyncio.wait_for(channel.channel_ready(), timeout=5.0)
        stub = custom_pb2_grpc.CustomServiceStub(channel)
        resp = await asyncio.wait_for(
            stub.Eval(custom_pb2.EvalRequest(lua=RUNWAYS_LUA_SNIPPET)), timeout=20.0
        )
    runways = parse_runways_json(resp.json)
    for rw in runways:
        if rw.airbase_name in WANT:
            print(
                f"{rw.airbase_name:<10} rwy {rw.name}: "
                f"lat={rw.lat:.6f} lon={rw.lon:.6f} "
                f"courseT={math.degrees(rw.course):.2f} "
                f"len={rw.length_m:.1f}m width={rw.width_m:.1f}m"
            )


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
