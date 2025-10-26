import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.qiniu_video_service import QiniuVideoService


@pytest.fixture
def video_service():
    with patch('app.services.qiniu_video_service.settings') as mock_settings:
        mock_settings.QINIU_API_KEY = "test_api_key"
        return QiniuVideoService()


@pytest.mark.asyncio
async def test_generate_video_success(video_service):
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = {"id": "video_123"}
        mock_response.raise_for_status = Mock()
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await video_service.generate_video("test prompt", "base64_image_data")
        
        assert "id" in result
        assert result["id"] == "video_123"


@pytest.mark.asyncio
async def test_check_video_status_success(video_service):
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = {"status": "Completed", "data": {"videos": [{"url": "http://video.url"}]}}
        mock_response.raise_for_status = Mock()
        
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await video_service.check_video_status("video_123")
        
        assert result["status"] == "Completed"


@pytest.mark.asyncio
async def test_poll_video_status_completed(video_service):
    with patch.object(video_service, 'check_video_status', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = {"status": "Completed", "data": {"videos": [{"url": "http://video.url"}]}}
        
        result = await video_service.poll_video_status("video_123", max_attempts=5)
        
        assert result["status"] == "Completed"


@pytest.mark.asyncio
async def test_poll_video_status_failed(video_service):
    with patch.object(video_service, 'check_video_status', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = {"status": "Failed", "message": "generation failed"}
        
        with pytest.raises(Exception, match="视频生成失败"):
            await video_service.poll_video_status("video_123", max_attempts=5)


@pytest.mark.asyncio
async def test_poll_video_status_timeout(video_service):
    with patch.object(video_service, 'check_video_status', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = {"status": "Processing"}
        
        with pytest.raises(Exception, match="视频生成超时"):
            await video_service.poll_video_status("video_123", max_attempts=2, initial_interval=0.01)
