import os
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import FileResponse
from typing import Optional

from app.models.tts import TTSRequest, TTSResponse
from app.services.tts_service import TTSService

router = APIRouter()
tts_service = TTSService()

@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(
    request: TTSRequest,
    x_api_key: Optional[str] = Header(None, description="API密钥（可选，用于认证）"),
    x_baidu_app_id: Optional[str] = Header(None, description="百度APP ID（使用百度TTS时需要）"),
    x_baidu_secret_key: Optional[str] = Header(None, description="百度Secret Key（使用百度TTS时需要）")
):
    api_key = x_api_key or os.getenv('TTS_API_KEY')
    app_id = x_baidu_app_id or os.getenv('BAIDU_APP_ID')
    secret_key = x_baidu_secret_key or os.getenv('BAIDU_SECRET_KEY')
    
    result = tts_service.text_to_speech(
        text=request.text,
        provider=request.provider,
        language=request.language,
        api_key=api_key,
        app_id=app_id,
        secret_key=secret_key
    )
    
    if result["success"]:
        audio_url = f"/api/tts/download/{result['audio_filename']}"
        return TTSResponse(
            success=True,
            message=result["message"],
            audio_url=audio_url,
            audio_filename=result["audio_filename"]
        )
    else:
        raise HTTPException(status_code=500, detail=result["message"])

@router.get("/tts/download/{filename}")
async def download_audio(filename: str):
    audio_path = tts_service.output_dir / filename
    
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="音频文件不存在")
    
    return FileResponse(
        path=str(audio_path),
        media_type="audio/mpeg",
        filename=filename
    )
