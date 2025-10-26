import httpx
from typing import Dict, Any
from app.core.config import settings


class QiniuImageService:
    
    def __init__(self):
        self.api_url = "https://openai.qiniu.com/v1/images/generations"
        api_key = settings.QINIU_API_KEY
        if isinstance(api_key, bytes):
            api_key = api_key.decode('utf-8')
        self.api_token = api_key.replace('Bearer ', '').strip() if api_key else ""
        self.character_cache = {}
        self.scene_cache = {}
    
    async def _simplify_text_to_prompt(self, text: str, llm_service: 'QiniuLLMService') -> str:
        llm_result = await llm_service.simplify_text_to_keywords(text)
        
        keywords = llm_result.get("keywords", "")
        scene = llm_result.get("scene", "")
        scene_summary = llm_result.get("scene_summary", "")
        character = llm_result.get("character", "")
        character_info = llm_result.get("character_info", "")
        
        if scene and scene_summary:
            self.scene_cache[scene] = scene_summary
        
        if character and character_info:
            self.character_cache[character] = character_info
        
        prompt_parts = []
        
        if scene and scene in self.scene_cache:
            prompt_parts.append(self.scene_cache[scene])
        elif scene_summary:
            prompt_parts.append(scene_summary)
        
        if character and character in self.character_cache:
            prompt_parts.append(self.character_cache[character])
        elif character_info:
            prompt_parts.append(character_info)
        
        if keywords:
            prompt_parts.append(keywords)
        
        prompt = ", ".join(prompt_parts) if prompt_parts else keywords
        
        return prompt[:200]
    
    async def text_to_images(self, text: str, llm_service: 'QiniuLLMService') -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        prompt = await self._simplify_text_to_prompt(text, llm_service)
        
        prompt_with_style = f"动漫风格, {prompt}"
        
        payload = {
            "model": "gemini-2.5-flash-image",
            "prompt": prompt_with_style,
            "n": 3,
            "size": "1024x1024"
        }
        
        async with httpx.AsyncClient(timeout=3600.0) as client:
            print(f"文生图 payload: {payload}")
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            print(f"文生图返回图片数量: {len(response.json()['data'])}")
            response.raise_for_status()
            return response.json()
