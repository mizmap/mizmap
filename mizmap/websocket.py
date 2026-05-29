"""WebSocket hub — fan-out of state events to all connected browsers."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

log = logging.getLogger(__name__)


class WebSocketHub:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    @property
    def client_count(self) -> int:
        """Number of connected browsers. Read without the lock — a stale-by-one
        count is fine for the fog poll's "anyone listening?" gate."""
        return len(self._clients)

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)
        log.info("ws connected — total clients: %d", len(self._clients))

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(ws)
        log.info("ws disconnected — total clients: %d", len(self._clients))

    async def broadcast(self, message: dict[str, Any]) -> None:
        payload = json.dumps(message, separators=(",", ":"))
        async with self._lock:
            targets = list(self._clients)
        if not targets:
            return
        # Best-effort: drop dead clients silently.
        results = await asyncio.gather(
            *(self._send(ws, payload) for ws in targets),
            return_exceptions=True,
        )
        dead = [ws for ws, r in zip(targets, results) if isinstance(r, Exception)]
        if dead:
            async with self._lock:
                for ws in dead:
                    self._clients.discard(ws)

    @staticmethod
    async def _send(ws: WebSocket, payload: str) -> None:
        await ws.send_text(payload)
