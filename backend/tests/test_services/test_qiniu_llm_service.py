import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.qiniu_llm_service import QiniuLLMService


@pytest.fixture
def llm_service():
    with patch('app.services.qiniu_llm_service.settings') as mock_settings:
        mock_settings.QINIU_API_KEY = "test_api_key"
        return QiniuLLMService()


@pytest.mark.asyncio
async def test_simplify_text_to_keywords_success(llm_service):
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"keywords": "test keywords", "scene": "test scene", "scene_summary": "test summary", "character": "test char", "character_info": "test info"}'
                }
            }]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await llm_service.simplify_text_to_keywords("test text")
        
        assert result["keywords"] == "test keywords"
        assert result["scene"] == "test scene"
        assert result["character"] == "test char"


@pytest.mark.asyncio
async def test_simplify_text_to_keywords_invalid_json(llm_service):
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "invalid json content"
                }
            }]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await llm_service.simplify_text_to_keywords("test text")
        
        assert "keywords" in result
        assert result["scene"] == ""
        assert result["character"] == ""
