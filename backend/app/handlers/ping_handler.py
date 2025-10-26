from fastapi import WebSocket
from typing import Dict, Any


async def handle_ping(websocket: WebSocket, message: Dict[str, Any]) -> None:
    await websocket.send_json({
        "type": "pong",
        "message": "心跳响应"
    })
