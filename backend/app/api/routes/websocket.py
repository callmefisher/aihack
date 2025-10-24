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
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()


qiniu_tts = QiniuTTSService()
qiniu_image = QiniuImageService()


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
                    # 发送处理开始消息
                    await websocket.send_json({
                        "type": "status",
                        "message": "开始处理TTS和图片生成...",
                        "text": text,
                        "paragraph_number": paragraph_number
                    })
                    
                    # 异步非阻塞方式处理图片生成
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
                    
                    # 启动后台图片生成任务（不等待完成）
                    asyncio.create_task(generate_images_background())
                    
                    try:
                        # 立即处理TTS，不等待图片生成
                        tts_result = await qiniu_tts.text_to_speech(text)
                        
                        # 立即发送TTS结果
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
                    # 发送处理开始消息
                    await websocket.send_json({
                        "type": "status",
                        "message": "开始生成视频...",
                        "paragraph_number": paragraph_number
                    })
                    
                    try:
                        # 模拟视频生成过程
                        output_dir = Path(f"output/{task_id}")
                        output_dir.mkdir(parents=True, exist_ok=True)
                        
                        video_path = output_dir / f"video_{paragraph_number}.mp4"
                        
                        if not video_path.exists():
                            # 下载示例视频
                            async with httpx.AsyncClient(timeout=120.0) as client:
                                response = await client.get("https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4")
                                if response.status_code == 200:
                                    with open(video_path, 'wb') as f:
                                        f.write(response.content)
                        
                        video_url = f"/output/{task_id}/video_{paragraph_number}.mp4"
                        
                        # 发送视频生成结果
                        await websocket.send_json({
                            "type": "video_result",
                            "video_url": video_url,
                            "paragraph_number": paragraph_number
                        })
                        
                    except httpx.HTTPError as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"视频生成失败: {str(e)}",
                            "paragraph_number": paragraph_number
                        })
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"视频生成失败: {str(e)}",
                            "paragraph_number": paragraph_number
                        })
                
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
