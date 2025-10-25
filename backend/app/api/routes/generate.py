from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import httpx
from app.services.tts_service import TTSService

router = APIRouter()
tts_service = TTSService()


class GenerateImageRequest(BaseModel):
    task_id: str
    text: str
    paragraph_number: int


class GenerateVideoRequest(BaseModel):
    task_id: str
    text: str
    paragraph_number: int
    image_url: str


class GenerateImageResponse(BaseModel):
    image_url: str
    audio_url: str


class GenerateVideoResponse(BaseModel):
    video_url: str


@router.post("/generate/image", response_model=GenerateImageResponse)
async def generate_image(request: GenerateImageRequest):
    try:
        output_dir = Path(f"output/{request.task_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        audio_path = output_dir / f"audio_{request.paragraph_number}.mp3"
        
        audio_url = None
        if not audio_path.exists():
            audio_result = await tts_service.text_to_speech(
                text=request.text,
                provider="qiniu",
                language="zh-CN",
                output_path=str(audio_path)
            )
            audio_url = f"/output/{request.task_id}/audio_{request.paragraph_number}.mp3"
        else:
            audio_url = f"/output/{request.task_id}/audio_{request.paragraph_number}.mp3"
        
        image_path = output_dir / f"image_{request.paragraph_number}.png"
        image_url = None
        
        if not image_path.exists():
            async with httpx.AsyncClient(timeout=3600.0) as client:
                response = await client.get(f"https://picsum.photos/800/600?random={request.paragraph_number}")
                if response.status_code == 200:
                    with open(image_path, 'wb') as f:
                        f.write(response.content)
                    image_url = f"/output/{request.task_id}/image_{request.paragraph_number}.png"
                else:
                    raise HTTPException(status_code=500, detail="Failed to generate image")
        else:
            image_url = f"/output/{request.task_id}/image_{request.paragraph_number}.png"
        
        return GenerateImageResponse(
            image_url=image_url,
            audio_url=audio_url
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/video", response_model=GenerateVideoResponse)
async def generate_video(request: GenerateVideoRequest):
    try:
        output_dir = Path(f"output/{request.task_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        video_path = output_dir / f"video_{request.paragraph_number}.mp4"
        
        if not video_path.exists():
            async with httpx.AsyncClient(timeout=3600.0) as client:
                response = await client.get("https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4")
                if response.status_code == 200:
                    with open(video_path, 'wb') as f:
                        f.write(response.content)
                else:
                    raise HTTPException(status_code=500, detail="Failed to generate video")
        
        video_url = f"/output/{request.task_id}/video_{request.paragraph_number}.mp4"
        
        return GenerateVideoResponse(video_url=video_url)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
