"""WebSocket connection manager for real-time dashboard updates."""
import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("privacy.websocket")


class ConnectionManager:
    def __init__(self):
        self._connections: list[WebSocket] = []
        self._lock = asyncio.Lock()
        self._loop = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        """Reference to the main event loop (set during app lifespan) so
        background capture threads can schedule broadcasts on it."""
        self._loop = loop

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._connections.append(websocket)
        logger.info("WebSocket client connected (%d active)", len(self._connections))

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)
        logger.info("WebSocket client disconnected (%d active)", len(self._connections))

    async def broadcast(self, message: dict[str, Any]):
        if not self._connections:
            return
        dead = []
        for websocket in list(self._connections):
            try:
                await websocket.send_json(message)
            except Exception as exc:  # pragma: no cover
                logger.debug("WebSocket send failed: %s", exc)
                dead.append(websocket)
        if dead:
            async with self._lock:
                for websocket in dead:
                    if websocket in self._connections:
                        self._connections.remove(websocket)

    def broadcast_sync(self, message: dict[str, Any]):
        """Thread-safe broadcast scheduled onto the running event loop.

        Safe to call from background capture threads. No-op when the loop is
        not available (e.g. before the app has started, or under tests).
        """
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        if not self._connections:
            return
        try:
            asyncio.run_coroutine_threadsafe(self.broadcast(message), loop)
        except (RuntimeError, Exception) as exc:  # pragma: no cover
            logger.debug("Broadcast scheduling failed: %s", exc)


manager = ConnectionManager()