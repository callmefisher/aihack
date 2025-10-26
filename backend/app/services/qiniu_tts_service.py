import httpx
import subprocess
import tempfile
import base64
import os
from pathlib import Path
from typing import Dict, Any
from app.core.config import settings


class QiniuTTSService:
    
    def __init__(self):
        self.api_url = "https://openai.qiniu.com/v1/voice/tts"
        api_key = settings.QINIU_API_KEY
        if isinstance(api_key, bytes):
            api_key = api_key.decode('utf-8')
        self.api_token = api_key.replace('Bearer ', '').strip() if api_key else ""
        self.background_music_path = Path(__file__).parent.parent.parent.parent / "ht.mp3"
    
    def mix_audio_with_background(self, tts_audio_base64: str) -> str:
        try:
            if not self.background_music_path.exists():
                print(f"背景音乐文件不存在: {self.background_music_path}，跳过ffmpeg混合，返回原始TTS音频")
                return tts_audio_base64
            
            if not self.background_music_path.is_file():
                print(f"背景音乐路径不是文件: {self.background_music_path}，跳过ffmpeg混合，返回原始TTS音频")
                return tts_audio_base64
            
            if not os.access(self.background_music_path, os.R_OK):
                print(f"背景音乐文件无读取权限: {self.background_music_path}，跳过ffmpeg混合，返回原始TTS音频")
                return tts_audio_base64
            
            print(f"背景音乐文件检查通过: {self.background_music_path}")
            
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"ffmpeg未安装或不可用: {str(e)}，跳过ffmpeg混合，返回原始TTS音频")
                return tts_audio_base64
            
            tts_audio_data = base64.b64decode(tts_audio_base64)
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tts_file:
                tts_file.write(tts_audio_data)
                tts_file_path = tts_file.name
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as output_file:
                output_file_path = output_file.name
            
            try:
                cmd = [
                    'ffmpeg',
                    '-i', tts_file_path,
                    '-i', str(self.background_music_path),
                    '-filter_complex', '[0:a]volume=1.0[a1];[1:a]volume=0.3[a2];[a1][a2]amix=inputs=2:duration=longest',
                    '-y',
                    output_file_path
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    print(f"ffmpeg混合失败 (返回码: {result.returncode})")
                    print(f"ffmpeg错误输出: {result.stderr}")
                    print(f"跳过ffmpeg混合，返回原始TTS音频")
                    return tts_audio_base64
                
                with open(output_file_path, 'rb') as f:
                    mixed_audio_data = f.read()
                
                mixed_audio_base64 = base64.b64encode(mixed_audio_data).decode('utf-8')
                print(f"音频混合成功: TTS长度={len(tts_audio_data)}, 混合后长度={len(mixed_audio_data)}")
                
                return mixed_audio_base64
                
            finally:
                try:
                    os.unlink(tts_file_path)
                    os.unlink(output_file_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"音频混合过程出错: {str(e)}，返回原始TTS音频")
            return tts_audio_base64
    
    async def text_to_speech(self, text: str, sequence_number: int = 0) -> Dict[str, Any]:
        print("step1 tts apitoken"+self.api_token)
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
        
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            if 'data' in result:
                original_audio_base64 = result['data']
                
                if sequence_number == 0:
                    print(f"TTS生成成功，序列号为0，开始混合背景音乐...")
                    mixed_audio_base64 = self.mix_audio_with_background(original_audio_base64)
                    result['data'] = mixed_audio_base64
                else:
                    print(f"TTS生成成功，序列号为{sequence_number}，跳过背景音乐混合")
            
            return result
