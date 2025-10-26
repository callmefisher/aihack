from fastapi import WebSocket
from typing import Dict, Any, List
import asyncio
import httpx
from app.services.qiniu_tts_service import QiniuTTSService
from app.services.qiniu_image_service import QiniuImageService
from app.services.qiniu_llm_service import QiniuLLMService


def split_text_by_punctuation(text: str) -> List[str]:
    import re
    sentences = re.split(r'([。！？；])', text)
    
    result = []
    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i]
        if i + 1 < len(sentences):
            punctuation = sentences[i + 1]
            sentence += punctuation
        
        sentence = sentence.strip()
        if sentence:
            result.append(sentence)
    
    if len(sentences) % 2 == 1:
        last_sentence = sentences[-1].strip()
        if last_sentence:
            result.append(last_sentence)
    
    return result


async def generate_images_background(
    full_paragraph_text: str, 
    para_num: int, 
    websocket: WebSocket,
    qiniu_image: QiniuImageService,
    qiniu_llm: QiniuLLMService
) -> None:
    try:
        print(f"开始生成图片，使用完整段落文本，长度={len(full_paragraph_text)}，段落号={para_num}")
        image_result = await qiniu_image.text_to_images(full_paragraph_text, qiniu_llm)
        await websocket.send_json({
            "type": "image_result",
            "data": image_result,
            "text": full_paragraph_text,
            "paragraph_number": para_num,
            "sequence_number": 0
        })
        print(f"图片生成成功，段落={para_num}")
        
    except httpx.TimeoutException as e:
        await websocket.send_json({
            "type": "error",
            "message": f"图片生成超时: {str(e)}",
            "paragraph_number": para_num,
            "sequence_number": 0
        })
    except httpx.HTTPError as e:
        await websocket.send_json({
            "type": "error",
            "message": f"图片生成失败: {str(e)}",
            "paragraph_number": para_num,
            "sequence_number": 0
        })
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"图片生成失败: {str(e)}",
            "paragraph_number": para_num,
            "sequence_number": 0
        })


async def handle_tts(
    websocket: WebSocket, 
    message: Dict[str, Any],
    qiniu_tts: QiniuTTSService,
    qiniu_image: QiniuImageService,
    qiniu_llm: QiniuLLMService
) -> None:
    text = message.get("text", "")
    paragraph_number = message.get("paragraph_number")
    sequence_number = message.get("sequence_number", 0)
    
    if not text:
        await websocket.send_json({
            "type": "error",
            "message": "文本内容不能为空"
        })
        return
    
    await websocket.send_json({
        "type": "status",
        "message": "开始处理TTS和图片生成...",
        "text": text,
        "paragraph_number": paragraph_number,
        "sequence_number": sequence_number
    })
    
    asyncio.create_task(generate_images_background(
        text, paragraph_number, websocket, qiniu_image, qiniu_llm
    ))
    
    try:
        sentences = split_text_by_punctuation(text)
        print(f"文本已分割为 {len(sentences)} 个句子")
        
        for idx, sentence in enumerate(sentences):
            print(f"处理句子 {idx + 1}/{len(sentences)}: {sentence[:30]}...")
            
            try:
                tts_result = await qiniu_tts.text_to_speech(sentence, sequence_number=idx)
                
                await websocket.send_json({
                    "type": "tts_result",
                    "data": tts_result,
                    "text": sentence,
                    "paragraph_number": paragraph_number,
                    "sequence_number": idx,
                    "sentence_index": idx + 1,
                    "total_sentences": len(sentences)
                })
                
                print(f"句子 {idx + 1} TTS完成")
                
            except httpx.HTTPError as e:
                print(f"句子 {idx + 1} TTS失败: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"句子 {idx + 1} TTS处理失败: {str(e)}",
                    "paragraph_number": paragraph_number,
                    "sequence_number": idx
                })
            except Exception as e:
                print(f"句子 {idx + 1} TTS异常: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"句子 {idx + 1} TTS处理失败: {str(e)}",
                    "paragraph_number": paragraph_number,
                    "sequence_number": idx
                })
        
        print(f"段落 {paragraph_number} 所有句子TTS完成")
        
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"TTS处理失败: {str(e)}",
            "paragraph_number": paragraph_number,
            "sequence_number": sequence_number
        })
