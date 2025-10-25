from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List
import json
import httpx
import asyncio
from pathlib import Path
from app.core.config import settings

router = APIRouter()


class QiniuTTSService:
    """七牛云TTS服务"""
    
    def __init__(self):
        self.api_url = "https://openai.qiniu.com/v1/voice/tts"
        self.api_token = settings.QINIU_API_KEY
    
    async def text_to_speech(self, text: str) -> Dict[str, Any]:
        """
        调用七牛云TTS API
        
        Args:
            text: 要转换的文本
            
        Returns:
            API响应数据
        """
        print("hello world1111")
        print(self.api_token)
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "audio": {
                "voice_type": "qiniu_zh_female_wwxkjx",
                "encoding": "mp3",
                "speed_ratio": 1.0
            },
            "request": {
                "text": text
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()


class QiniuImageService:
    """七牛云文生图服务"""
    
    def __init__(self):
        self.api_url = "https://openai.qiniu.com/v1/images/generations"
        self.api_token = settings.QINIU_API_KEY
    
    def _simplify_text_to_prompt(self, text: str) -> str:
        """
        将原始文本精简为关键字(人物、场景等)
        
        Args:
            text: 原始文本
            
        Returns:
            精简后的prompt
        """
        prompt = text[:200]
        return prompt
    
    async def text_to_images(self, text: str) -> Dict[str, Any]:
        """
        调用七牛云文生图API
        
        Args:
            text: 要转换的文本
            
        Returns:
            API响应数据，包含base64编码的图片数据
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        prompt = self._simplify_text_to_prompt(text)
        
        payload = {
            "model": "gemini-2.5-flash-image",
            "prompt": prompt,
            "n": 3,
            "size": "1024x1024"
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            print(payload)
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            print(len(response.json()["data"]))
            print(payload)
            response.raise_for_status()
            return response.json()


class QiniuVideoService:
    """七牛云视频生成服务"""
    
    def __init__(self):
        self.api_url = "https://openai.qiniu.com/v1/videos/generations"
        self.api_token = settings.QINIU_API_KEY
    
    async def generate_video(self, prompt: str, image_base64: str) -> Dict[str, Any]:
        """
        调用七牛云视频生成API
        
        Args:
            prompt: 视频生成提示词
            image_base64: base64编码的图片数据
            
        Returns:
            API响应数据，包含视频生成任务ID
        """
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
            "model": "veo-3.0-fast-generate-preview"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def check_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        查询视频生成状态
        
        Args:
            video_id: 视频生成任务ID
            
        Returns:
            API响应数据，包含视频生成状态和URL
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.api_url}/{video_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def poll_video_status(self, video_id: str, max_attempts: int = 60, interval: int = 5) -> Dict[str, Any]:
        """
        周期性查询视频生成状态，直到完成
        
        Args:
            video_id: 视频生成任务ID
            max_attempts: 最大查询次数
            interval: 查询间隔（秒）
            
        Returns:
            完成后的API响应数据
        """
        for attempt in range(max_attempts):
            result = await self.check_video_status(video_id)
            
            if result.get("status") == "Completed":
                return result
            elif result.get("status") == "Failed":
                raise Exception(f"视频生成失败: {result.get('message', '未知错误')}")
            
            await asyncio.sleep(interval)
        
        raise Exception(f"视频生成超时，已尝试 {max_attempts} 次")


qiniu_tts = QiniuTTSService()
qiniu_image = QiniuImageService()
qiniu_video = QiniuVideoService()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket端点，接收文本并流式返回TTS结果
    """
    await websocket.accept()
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            
            try:
                # 解析JSON数据
                message = json.loads(data)
                text = message.get("text", "")
                action = message.get("action", "tts")
                paragraph_number = message.get("paragraph_number")
                task_id = message.get("task_id")
                image_url = message.get("image_url")
                
                if not text and action != "video":
                    await websocket.send_json({
                        "type": "error",
                        "message": "文本内容不能为空"
                    })
                    continue
                
                # 处理TTS请求
                if action == "tts":
                    await websocket.send_json({
                        "type": "status",
                        "message": "开始处理TTS和图片生成...",
                        "text": text,
                        "paragraph_number": paragraph_number
                    })
                    
                    async def generate_images_background():
                        """后台生成图片，不阻塞TTS返回"""
                        try:
                            image_result = await qiniu_image.text_to_images(text)
                            await websocket.send_json({
                                "type": "image_result",
                                "data": image_result,
                                "text": text,
                                "paragraph_number": paragraph_number
                            })
                            
                        except httpx.TimeoutException as e:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"图片生成超时: {str(e)}",
                                "paragraph_number": paragraph_number
                            })
                        except httpx.HTTPError as e:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"图片生成失败: {str(e)}",
                                "paragraph_number": paragraph_number
                            })
                        except Exception as e:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"图片生成失败: {str(e)}",
                                "paragraph_number": paragraph_number
                            })
                    
                    asyncio.create_task(generate_images_background())
                    
                    try:
                        tts_result = await qiniu_tts.text_to_speech(text)
                        
                        await websocket.send_json({
                            "type": "tts_result",
                            "data": tts_result,
                            "text": text,
                            "paragraph_number": paragraph_number
                        })
                        
                    except httpx.HTTPError as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"TTS处理失败: {str(e)}",
                            "paragraph_number": paragraph_number
                        })
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"TTS处理失败: {str(e)}",
                            "paragraph_number": paragraph_number
                        })
                
                # 处理视频生成请求
                elif action == "video":
                    image_base64 = message.get("image_base64", "")
                    
                    if not image_base64:
                        await websocket.send_json({
                            "type": "error",
                            "message": "图片数据不能为空",
                            "paragraph_number": paragraph_number
                        })
                        continue
                    
                    await websocket.send_json({
                        "type": "status",
                        "message": "开始生成视频...",
                        "paragraph_number": paragraph_number
                    })
                    
                    async def generate_video_background():
                        """后台生成视频，不阻塞WebSocket"""
                        try:
                            video_init_result = await qiniu_video.generate_video(text, image_base64)
                            video_id = video_init_result.get("id")
                            
                            if video_id:
                                video_final_result = await qiniu_video.poll_video_status(video_id)
                                
                                if video_final_result.get("status") == "Completed":
                                    videos = video_final_result.get("data", {}).get("videos", [])
                                    if videos and len(videos) > 0:
                                        video_url = videos[0].get("url")
                                        await websocket.send_json({
                                            "type": "video_result",
                                            "video_url": video_url,
                                            "paragraph_number": paragraph_number
                                        })
                        except Exception as e:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"视频生成失败: {str(e)}",
                                "paragraph_number": paragraph_number
                            })
                    
                    asyncio.create_task(generate_video_background())
                
                # 发送完成消息
                await websocket.send_json({
                    "type": "complete",
                    "message": "处理完成"
                })
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "无效的JSON格式"
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"处理错误: {str(e)}"
                })
    
    except WebSocketDisconnect:
        print("WebSocket连接已断开")
    except Exception as e:
        print(f"WebSocket错误: {str(e)}")
        try:
            await websocket.close()
        except:
            pass
