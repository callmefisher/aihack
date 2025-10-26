import httpx
from typing import Dict, Any
from app.core.config import settings


class QiniuLLMService:
    
    def __init__(self):
        self.api_url = "https://openai.qiniu.com/v1/chat/completions"
        api_key = settings.QINIU_API_KEY
        if isinstance(api_key, bytes):
            api_key = api_key.decode('utf-8')
        self.api_token = api_key.replace('Bearer ', '').strip() if api_key else ""
    
    async def simplify_text_to_keywords(self, text: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        system_prompt = """你是一个专业的文本摘要助手。请将输入的文本段落精简为关键字描述。
要求：
1. 必须提取场景关键词（场景描述、环境、氛围等）
2. 如果包含角色，必须返回角色名称、特点、性格、外貌等详细信息
3. 输出格式为JSON: {"keywords": "关键字描述", "scene": "场景名称或类型", "scene_summary": "场景详细描述摘要", "character": "角色名称", "character_info": "角色详细信息"}
4. 如果没有明确的角色，character和character_info为空字符串
5. 如果没有明确的场景，scene和scene_summary为空字符串
6. keywords必须精简到120个字符以内
7. scene_summary和character_info需要包含足够详细的信息以保证图片风格一致性"""
        
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "model": "deepseek-v3",
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            try:
                import json as json_module
                parsed = json_module.loads(content)
                return {
                    "keywords": parsed.get("keywords", "")[:120],
                    "scene": parsed.get("scene", ""),
                    "scene_summary": parsed.get("scene_summary", ""),
                    "character": parsed.get("character", ""),
                    "character_info": parsed.get("character_info", "")
                }
            except:
                return {
                    "keywords": content[:120],
                    "scene": "",
                    "scene_summary": "",
                    "character": "",
                    "character_info": ""
                }
