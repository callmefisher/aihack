import pytest
from unittest.mock import Mock, AsyncMock
from app.handlers.ping_handler import handle_ping


@pytest.mark.asyncio
async def test_handle_ping():
    mock_websocket = Mock()
    mock_websocket.send_json = AsyncMock()
    
    message = {"action": "ping"}
    
    await handle_ping(mock_websocket, message)
    
    mock_websocket.send_json.assert_called_once()
    call_args = mock_websocket.send_json.call_args[0][0]
    assert call_args["type"] == "pong"
    assert call_args["message"] == "心跳响应"
