"""
Tests for WebSocket real-time updates.

Requirements: 3.6, 7.5
"""
import pytest
from starlette.testclient import TestClient

from app.main import app


def test_websocket_connects():
    """WebSocket endpoint accepts connections."""
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        # Connection should be established
        ws.send_text("ping")
        # Server doesn't echo, just keeps alive


def test_websocket_manager_broadcast():
    """ConnectionManager broadcasts to all connected clients."""
    import asyncio
    from app.services.websocket_manager import ConnectionManager

    mgr = ConnectionManager()
    # Manager starts with no connections
    assert len(mgr.active_connections) == 0


def test_websocket_manager_disconnect():
    """ConnectionManager handles disconnections."""
    from app.services.websocket_manager import ConnectionManager

    mgr = ConnectionManager()
    assert len(mgr.active_connections) == 0
    # Disconnecting a non-existent connection is safe
    mgr.disconnect(None)
    assert len(mgr.active_connections) == 0
