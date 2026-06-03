"""One-off: read the mission's calendar date and DCS's magnetic declination at a
fixed point, to confirm DCS's declination is era-dependent (tracks the mission
year) rather than sign-buggy.

    MIZMAP_GRPC_HOST=192.168.1.116 uv run python scripts/diag_missiondate.py
"""

from __future__ import annotations

import asyncio
import json
import os

import grpc

import mizmap.proto_gen  # noqa: F401  -- sets sys.path for generated imports
from dcs.custom.v0 import custom_pb2, custom_pb2_grpc

DATE_LUA = "return { year = env.mission.date.Year, month = env.mission.date.Month, day = env.mission.date.Day }"

# Kandahar reference point (matches the runway diagnostic).
KANDAHAR = (31.506, 65.848)


async def main() -> None:
    host = os.environ.get("MIZMAP_GRPC_HOST", "127.0.0.1")
    port = int(os.environ.get("MIZMAP_GRPC_PORT", "50051"))
    async with grpc.aio.insecure_channel(f"{host}:{port}") as channel:
        await asyncio.wait_for(channel.channel_ready(), timeout=5.0)
        stub = custom_pb2_grpc.CustomServiceStub(channel)

        date_resp = await asyncio.wait_for(
            stub.Eval(custom_pb2.EvalRequest(lua=DATE_LUA)), timeout=10.0
        )
        date = json.loads(date_resp.json)

        lat, lon = KANDAHAR
        decl_resp = await asyncio.wait_for(
            stub.GetMagneticDeclination(
                custom_pb2.GetMagneticDeclinationRequest(lat=lat, lon=lon, alt=0.0)
            ),
            timeout=10.0,
        )

    print(f"mission date : {date.get('year')}-{date.get('month'):02d}-{date.get('day'):02d}")
    print(f"DCS declination @ Kandahar ({lat}, {lon}) : {float(decl_resp.declination):+.2f}°")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
