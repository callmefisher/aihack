import httpx
import asyncio
from typing import Dict, Any, Callable
from app.core.config import settings


class QiniuVideoService:
    
    def __init__(self):
        # self.api_url = "https://openai.qiniu.com/v1/videos/generations"
        self.api_url = "https://api.qnaigc.com/v1/videos/generations"
        api_key = settings.QINIU_API_KEY
        if isinstance(api_key, bytes):
            api_key = api_key.decode('utf-8')
        self.api_token = api_key.replace('Bearer ', '').strip() if api_key else ""
    
    async def generate_video(self, prompt: str, image_base64: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "instances": [
                {
                    "prompt": prompt,
                    "image": {
                        "bytesBase64Encoded": image_base64,
                        "mimeType": "image/png"
                    }
                }
            ],
            "parameters": {
                "generateAudio": True,
                "durationSeconds": 8,
                "sampleCount": 1
            },
            "model": "veo-3.1-fast-generate-preview"
        }
        
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def check_video_status(self, video_id: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.api_url}/{video_id}"
        
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def poll_video_status(
        self, 
        video_id: str, 
        max_attempts: int = 1500, 
        initial_interval: float = 1.0, 
        max_interval: float = 3.0, 
        progress_callback: Callable = None
    ) -> Dict[str, Any]:
        current_interval = initial_interval
        
        for attempt in range(max_attempts):
            result = await self.check_video_status(video_id)
            
            if result.get("status") == "Completed":
                return result
            elif result.get("status") == "Failed":
                raise Exception(f"视频生成失败: {result.get('message', '未知错误')}")
            
            if progress_callback:
                await progress_callback(attempt, max_attempts)
            
            await asyncio.sleep(current_interval)
            
            current_interval = min(current_interval * 1.2, max_interval)
        
        raise Exception(f"视频生成超时，已尝试 {max_attempts} 次")
