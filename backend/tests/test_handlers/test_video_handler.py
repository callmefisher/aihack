import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.handlers.video_handler import handle_video


@pytest.mark.asyncio
async def test_handle_video_empty_image():
    mock_websocket = Mock()
    mock_websocket.send_json = AsyncMock()
    
    message = {"image_base64": "", "text": "test", "paragraph_number": 1, "sequence_number": 0}
    mock_video = Mock()
    mock_llm = Mock()
    
    await handle_video(mock_websocket, message, mock_video, mock_llm)
    
    call_args = mock_websocket.send_json.call_args[0][0]
    assert call_args["type"] == "error"
    assert "不能为空" in call_args["message"]


@pytest.mark.asyncio
async def test_handle_video_success():
    mock_websocket = Mock()
    mock_websocket.send_json = AsyncMock()
    mock_websocket.client_state.value = 1
    
    message = {
        "image_base64": "base64_image_data",
        "text": "test text",
        "paragraph_number": 1,
        "sequence_number": 0
    }
    
    mock_video = Mock()
    mock_llm = Mock()
    
    with patch('asyncio.create_task'):
        await handle_video(mock_websocket, message, mock_video, mock_llm)
    
    assert mock_websocket.send_json.call_count >= 1
    call_args = mock_websocket.send_json.call_args[0][0]
    assert call_args["type"] == "status"
