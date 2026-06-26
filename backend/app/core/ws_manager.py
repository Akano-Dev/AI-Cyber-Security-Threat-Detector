"""WebSocket connection manager for broadcasting live threat events."""
import json

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._clients: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._clients.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self._clients:
            self._clients.remove(ws)

    @property
    def count(self) -> int:
        return len(self._clients)

    async def broadcast(self, data: dict):
        message = json.dumps(data)
        for ws in list(self._clients):
            try:
                await ws.send_text(message)
            except Exception:
                self.disconnect(ws)


manager = ConnectionManager()
