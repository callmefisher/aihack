import pytest
from unittest.mock import Mock, patch, AsyncMock
import base64
from app.services.qiniu_tts_service import QiniuTTSService


@pytest.fixture
def tts_service():
    with patch('app.services.qiniu_tts_service.settings') as mock_settings:
        mock_settings.QINIU_API_KEY = "test_api_key"
        return QiniuTTSService()


@pytest.mark.asyncio
async def test_text_to_speech_success(tts_service):
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = {"data": base64.b64encode(b"test_audio").decode()}
        mock_response.raise_for_status = Mock()
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await tts_service.text_to_speech("test text", sequence_number=1)
        
        assert "data" in result
        assert isinstance(result["data"], str)


@pytest.mark.asyncio
async def test_text_to_speech_with_background_music(tts_service):
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = {"data": base64.b64encode(b"test_audio").decode()}
        mock_response.raise_for_status = Mock()
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        with patch.object(tts_service, 'mix_audio_with_background', return_value="mixed_audio"):
            result = await tts_service.text_to_speech("test text", sequence_number=0)
            
            assert "data" in result


def test_mix_audio_with_background_missing_file(tts_service):
    with patch('pathlib.Path.exists', return_value=False):
        original_audio = base64.b64encode(b"test_audio").decode()
        result = tts_service.mix_audio_with_background(original_audio)
        
        assert result == original_audio


def test_mix_audio_with_background_success(tts_service):
    with patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.is_file', return_value=True), \
         patch('os.access', return_value=True), \
         patch('subprocess.run') as mock_subprocess:
        
        mock_subprocess.side_effect = [
            Mock(returncode=0),
            Mock(returncode=0)
        ]
        
        original_audio = base64.b64encode(b"test_audio").decode()
        
        with patch('tempfile.NamedTemporaryFile'), \
             patch('builtins.open', create=True), \
             patch('os.unlink'):
            result = tts_service.mix_audio_with_background(original_audio)
