import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.qiniu_image_service import QiniuImageService
from app.services.qiniu_llm_service import QiniuLLMService


@pytest.fixture
def image_service():
    with patch('app.services.qiniu_image_service.settings') as mock_settings:
        mock_settings.QINIU_API_KEY = "test_api_key"
        return QiniuImageService()


@pytest.fixture
def llm_service():
    with patch('app.services.qiniu_llm_service.settings') as mock_settings:
        mock_settings.QINIU_API_KEY = "test_api_key"
        return QiniuLLMService()


@pytest.mark.asyncio
async def test_text_to_images_success(image_service, llm_service):
    with patch('httpx.AsyncClient') as mock_client:
        mock_llm_response = Mock()
        mock_llm_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"keywords": "test", "scene": "room", "scene_summary": "a room", "character": "john", "character_info": "a man"}'
                }
            }]
        }
        mock_llm_response.raise_for_status = Mock()
        
        mock_image_response = Mock()
        mock_image_response.json.return_value = {"data": ["image1", "image2", "image3"]}
        mock_image_response.raise_for_status = Mock()
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(side_effect=[mock_llm_response, mock_image_response])
        
        result = await image_service.text_to_images("test text", llm_service)
        
        assert "data" in result
        assert len(result["data"]) == 3


@pytest.mark.asyncio
async def test_simplify_text_to_prompt_caching(image_service, llm_service):
    with patch.object(llm_service, 'simplify_text_to_keywords', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {
            "keywords": "test",
            "scene": "room",
            "scene_summary": "a beautiful room",
            "character": "john",
            "character_info": "a tall man"
        }
        
        result1 = await image_service._simplify_text_to_prompt("test text", llm_service)
        
        assert "room" in image_service.scene_cache
        assert "john" in image_service.character_cache
        assert image_service.scene_cache["room"] == "a beautiful room"
        assert image_service.character_cache["john"] == "a tall man"
