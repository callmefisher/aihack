import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from novel_to_anime.generators.audio import TextToSpeech

class TTSService:
    def __init__(self):
        self.output_dir = Path("backend/output/audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def text_to_speech(
        self, 
        text: str, 
        provider: str = "azure",
        language: str = "zh-CN",
        api_key: str = None,
        app_id: str = None,
        secret_key: str = None
    ) -> dict:
        try:
            audio_filename = f"{uuid.uuid4()}.mp3"
            output_path = self.output_dir / audio_filename
            
            tts = TextToSpeech(
                api_key=api_key,
                provider=provider,
                app_id=app_id,
                secret_key=secret_key
            )
            
            result_path = tts.generate_speech(text, str(output_path), language)
            
            return {
                "success": True,
                "message": "语音生成成功",
                "audio_path": str(result_path),
                "audio_filename": audio_filename
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"语音生成失败: {str(e)}",
                "audio_path": None,
                "audio_filename": None
            }
