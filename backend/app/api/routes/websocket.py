from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import json
from app.services.qiniu_tts_service import QiniuTTSService
from app.services.qiniu_llm_service import QiniuLLMService
from app.services.qiniu_image_service import QiniuImageService
from app.services.qiniu_video_service import QiniuVideoService
from app.handlers import handle_ping, handle_tts, handle_video

router = APIRouter()

WEBSOCKET_HEARTBEAT_TIMEOUT = 200000
WEBSOCKET_PING_INTERVAL = 200000

qiniu_tts = QiniuTTSService()
qiniu_llm = QiniuLLMService()
qiniu_image = QiniuImageService()
qiniu_video = QiniuVideoService()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                text = message.get("text", "")
                action = message.get("action", "tts")
                paragraph_number = message.get("paragraph_number")
                task_id = message.get("task_id")
                image_url = message.get("image_url")
                
                print(f"=== 收到WebSocket消息 ===")
                print(f"action: {action}")
                print(f"paragraph_number: {paragraph_number}")
                print(f"task_id: {task_id}")
                print(f"text_length: {len(text) if text else 0}")
                
                if action == "ping":
                    await handle_ping(websocket, message)
                    continue
                
                if not text and action not in ["video"]:
                    await websocket.send_json({
                        "type": "error",
                        "message": "文本内容不能为空"
                    })
                    continue
                
                if action == "tts":
                    await handle_tts(websocket, message, qiniu_tts, qiniu_image, qiniu_llm)
                
                elif action == "video":
                    await handle_video(websocket, message, qiniu_video, qiniu_llm)
                
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
        pass
    except Exception as e:
        print(f"WebSocket错误: {str(e)}")
        try:
            await websocket.close()
        except:
            pass
