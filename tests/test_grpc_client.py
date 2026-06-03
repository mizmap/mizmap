"""Unit tests for the DCS-gRPC client.

Focus: the magnetic-declination sign correction. DCS-gRPC 0.8.1 returns the
value with the sign inverted relative to its own proto contract, so
`fetch_declination` negates it (see the method docstring + proto/UPSTREAM.md).
"""

from __future__ import annotations

import pytest

import mizmap.proto_gen  # noqa: F401  -- sets sys.path for generated imports
from mizmap import grpc_client


async def _noop(*args, **kwargs):
    return None


def _make_client() -> grpc_client.DcsGrpcClient:
    return grpc_client.DcsGrpcClient(
        host="127.0.0.1",
        port=50051,
        on_status=_noop,
        on_unit=_noop,
        on_unit_gone=_noop,
        on_disconnect=_noop,
        on_mission_start=_noop,
        on_mission_end=_noop,
        on_mark_add=_noop,
        on_mark_remove=_noop,
    )


class _FakeResp:
    def __init__(self, declination: float) -> None:
        self.declination = declination


class _FakeStub:
    def __init__(self, value: float) -> None:
        self._value = value

    async def GetMagneticDeclination(self, request):  # noqa: N802 -- proto method name
        return _FakeResp(self._value)


def _patch_stub(monkeypatch, value: float) -> None:
    monkeypatch.setattr(
        grpc_client.custom_pb2_grpc,
        "CustomServiceStub",
        lambda channel: _FakeStub(value),
    )


async def test_declination_easterly_point_is_negated(monkeypatch):
    # Kandahar reads +2.9°E on the DCS F10 compass rose; gRPC reports -2.29.
    # We must hand callers the sign-corrected easterly (+) value.
    client = _make_client()
    client._channel = object()  # non-None so the RPC path runs
    _patch_stub(monkeypatch, -2.29)

    result = await client.fetch_declination(31.51, 65.85)
    assert result == pytest.approx(2.29)


async def test_declination_westerly_point_is_negated(monkeypatch):
    # New York is ~13°W (negative) in reality; gRPC reports it as +13.03.
    # The negation flips it back to the correct westerly (-) value.
    client = _make_client()
    client._channel = object()
    _patch_stub(monkeypatch, 13.03)

    result = await client.fetch_declination(40.71, -74.01)
    assert result == pytest.approx(-13.03)


async def test_declination_none_without_channel():
    client = _make_client()
    client._channel = None
    assert await client.fetch_declination(31.51, 65.85) is None
