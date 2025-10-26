from fastapi import WebSocket
from typing import Dict, Any
import asyncio
from app.services.qiniu_video_service import QiniuVideoService
from app.services.qiniu_llm_service import QiniuLLMService


async def generate_video_background(
    text: str,
    image_base64: str,
    para_num: int,
    seq_num: int,
    websocket: WebSocket,
    qiniu_video: QiniuVideoService,
    qiniu_llm: QiniuLLMService
) -> None:
    try:
        llm_result = await qiniu_llm.simplify_text_to_keywords(text)
        video_prompt = llm_result.get("keywords", text[:200])
        
        print(f"step1 image2video request - original text: {text}")
        print(f"step1 image2video request - LLM generated prompt: {video_prompt}")
        print(f"step1 image2video request - image base64 length: {len(image_base64)}")
        print(f"step1 image2video request - paragraph_number: {para_num}, sequence_number: {seq_num}")
        
        video_init_result = await qiniu_video.generate_video(video_prompt, image_base64)
        video_id = video_init_result.get("id")
        print("step2 image2video response taskid " + video_id)
        
        if video_id:
            async def send_progress(attempt, max_attempts):
                if websocket.client_state.value == 1:
                    progress_percent = int((attempt / max_attempts) * 100)
                    await websocket.send_json({
                        "type": "video_progress",
                        "message": f"视频生成中... {progress_percent}%",
                        "progress": progress_percent,
                        "paragraph_number": para_num,
                        "sequence_number": seq_num
                    })
            
            video_final_result = await qiniu_video.poll_video_status(
                video_id,
                progress_callback=send_progress
            )
            print("step3 image2video response task status " + video_final_result.get("status"))
            
            if video_final_result.get("status") == "Completed":
                videos = video_final_result.get("data", {}).get("videos", [])
                if videos and len(videos) > 0:
                    video_url = videos[0].get("url")
                    if websocket.client_state.value == 1:
                        await websocket.send_json({
                            "type": "video_result",
                            "video_url": video_url,
                            "paragraph_number": para_num,
                            "sequence_number": seq_num
                        })
    except Exception as e:
        print(f"视频生成错误: {str(e)}")
        try:
            if websocket.client_state.value == 1:
                await websocket.send_json({
                    "type": "error",
                    "message": f"视频生成失败: {str(e)}",
                    "paragraph_number": para_num,
                    "sequence_number": seq_num
                })
        except:
            pass


async def handle_video(
    websocket: WebSocket,
    message: Dict[str, Any],
    qiniu_video: QiniuVideoService,
    qiniu_llm: QiniuLLMService
) -> None:
    print(f"=== 处理视频生成请求 ===")
    image_base64 = message.get("image_base64", "")
    text = message.get("text", "")
    paragraph_number = message.get("paragraph_number")
    sequence_number = message.get("sequence_number", 0)
    
    print(f"image_base64_length: {len(image_base64) if image_base64 else 0}")
    print(f"text: {text[:50] if text else 'empty'}...")
    print(f"paragraph_number: {paragraph_number}")
    print(f"sequence_number: {sequence_number}")
    
    if not image_base64:
        print(f"❌ 图片数据为空，返回错误")
        await websocket.send_json({
            "type": "error",
            "message": "图片数据不能为空",
            "paragraph_number": paragraph_number,
            "sequence_number": sequence_number
        })
        return
    
    print(f"✅ 发送视频生成开始状态")
    await websocket.send_json({
        "type": "status",
        "message": "开始生成视频...",
        "paragraph_number": paragraph_number,
        "sequence_number": sequence_number
    })
    
    asyncio.create_task(generate_video_background(
        text, image_base64, paragraph_number, sequence_number,
        websocket, qiniu_video, qiniu_llm
    ))
