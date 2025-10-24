from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
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


qiniu_tts = QiniuTTSService()


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
                
                if not text:
                    await websocket.send_json({
                        "type": "error",
                        "message": "文本内容不能为空"
                    })
                    continue
                
                # 发送处理开始消息
                await websocket.send_json({
                    "type": "status",
                    "message": "开始处理文本...",
                    "text": text
                })
                
                # 处理TTS请求
                if action == "tts":
                    try:
                        # 调用七牛云TTS API
                        tts_result = await qiniu_tts.text_to_speech(text)
                        
                        # 发送TTS结果
                        await websocket.send_json({
                            "type": "tts_result",
                            "data": tts_result,
                            "text": text
                        })
                        
                    except httpx.HTTPError as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"TTS API调用失败: {str(e)}"
                        })
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"TTS处理失败: {str(e)}"
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
