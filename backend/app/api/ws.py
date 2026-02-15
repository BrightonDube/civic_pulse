"""
WebSocket API endpoint for real-time updates.

Requirements: 3.6, 7.5
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket_manager import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time report and status updates.
    Clients receive JSON messages with event types:
    - new_report: when a new report is created
    - status_change: when a report status is updated
    - leaderboard_update: when leaderboard changes
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, receive any client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
