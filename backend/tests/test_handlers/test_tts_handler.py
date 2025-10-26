import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.handlers.tts_handler import handle_tts, split_text_by_punctuation


def test_split_text_by_punctuation():
    text = "第一句。第二句！第三句？"
    result = split_text_by_punctuation(text)
    
    assert len(result) == 3
    assert result[0] == "第一句。"
    assert result[1] == "第二句！"
    assert result[2] == "第三句？"


def test_split_text_by_punctuation_no_punctuation():
    text = "没有标点符号"
    result = split_text_by_punctuation(text)
    
    assert len(result) == 1
    assert result[0] == "没有标点符号"


@pytest.mark.asyncio
async def test_handle_tts_empty_text():
    mock_websocket = Mock()
    mock_websocket.send_json = AsyncMock()
    
    message = {"text": "", "paragraph_number": 1}
    mock_tts = Mock()
    mock_image = Mock()
    mock_llm = Mock()
    
    await handle_tts(mock_websocket, message, mock_tts, mock_image, mock_llm)
    
    call_args = mock_websocket.send_json.call_args[0][0]
    assert call_args["type"] == "error"
    assert "不能为空" in call_args["message"]


@pytest.mark.asyncio
async def test_handle_tts_success():
    mock_websocket = Mock()
    mock_websocket.send_json = AsyncMock()
    
    message = {"text": "测试文本。", "paragraph_number": 1, "sequence_number": 0}
    
    mock_tts = Mock()
    mock_tts.text_to_speech = AsyncMock(return_value={"data": "audio_data"})
    
    mock_image = Mock()
    mock_image.text_to_images = AsyncMock(return_value={"data": ["image1"]})
    
    mock_llm = Mock()
    
    with patch('asyncio.create_task'):
        await handle_tts(mock_websocket, message, mock_tts, mock_image, mock_llm)
    
    assert mock_websocket.send_json.call_count >= 2
