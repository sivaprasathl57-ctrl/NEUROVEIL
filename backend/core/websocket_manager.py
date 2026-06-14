from fastapi import WebSocket
from typing import Dict, List
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = []
        self.active_connections[room].append(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.active_connections:
            self.active_connections[room].remove(websocket)

    async def send_to_room(self, message: str, room: str):
        if room in self.active_connections:
            dead = []
            for connection in self.active_connections[room]:
                try:
                    await connection.send_text(message)
                except:
                    dead.append(connection)
            for d in dead:
                self.active_connections[room].remove(d)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            pass

    async def broadcast(self, message: str):
        for room, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_text(message)
                except:
                    pass
