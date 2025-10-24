import os
import base64
import json


class TextToSpeech:
    def __init__(self, api_key: str = None, provider: str = "azure", app_id: str = None, secret_key: str = None):
        self.api_key = api_key or os.getenv('TTS_API_KEY')
        self.provider = provider
        self.app_id = app_id or os.getenv('BAIDU_APP_ID')
        self.secret_key = secret_key or os.getenv('BAIDU_SECRET_KEY')
    
    def generate_speech(self, text: str, output_path: str, language: str = "zh-CN") -> str:
        if self.provider == "azure":
            if not self.api_key:
                print(f"⚠️ 警告: 未配置Azure TTS API密钥，将生成静音音频")
                return self._generate_silence(output_path, duration=len(text) * 0.2)
            return self._generate_azure_tts(text, output_path, language)
        
        elif self.provider == "openai":
            if not self.api_key:
                print(f"⚠️ 警告: 未配置OpenAI TTS API密钥，将生成静音音频")
                return self._generate_silence(output_path, duration=len(text) * 0.2)
            return self._generate_openai_tts(text, output_path)
        
        elif self.provider == "baidu":
            if not self.api_key or not self.secret_key:
                print(f"⚠️ 警告: 未配置百度TTS API密钥，将生成静音音频")
                return self._generate_silence(output_path, duration=len(text) * 0.2)
            return self._generate_baidu_tts(text, output_path, language)
        
        else:
            raise ValueError(f"不支持的TTS提供商: {self.provider}")
    
    def _generate_silence(self, output_path: str, duration: float) -> str:
        from pydub import AudioSegment
        
        silence = AudioSegment.silent(duration=int(duration * 1000))
        silence.export(output_path, format="mp3")
        
        return output_path
    
    def _generate_azure_tts(self, text: str, output_path: str, language: str) -> str:
        import azure.cognitiveservices.speech as speechsdk
        
        speech_config = speechsdk.SpeechConfig(subscription=self.api_key)
        speech_config.speech_synthesis_language = language
        
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
        
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        result = synthesizer.speak_text_async(text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return output_path
        else:
            raise Exception(f"语音合成失败: {result.reason}")
    
    def _generate_openai_tts(self, text: str, output_path: str) -> str:
        import openai
        
        openai.api_key = self.api_key
        
        response = openai.Audio.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return output_path
    
    def _generate_baidu_tts(self, text: str, output_path: str, language: str) -> str:
        import requests
        
        token_url = "https://aip.baidubce.com/oauth/2.0/token"
        token_params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        
        token_response = requests.get(token_url, params=token_params)
        if token_response.status_code != 200:
            raise Exception(f"获取百度访问令牌失败: {token_response.text}")
        
        access_token = token_response.json().get("access_token")
        
        tts_url = "https://tsn.baidu.com/text2audio"
        
        lang_map = {
            "zh-CN": "zh",
            "en-US": "en"
        }
        lang_code = lang_map.get(language, "zh")
        
        tts_params = {
            "tok": access_token,
            "tex": text,
            "per": 0,
            "spd": 5,
            "pit": 5,
            "vol": 5,
            "aue": 3,
            "cuid": self.app_id or "novel_to_anime",
            "lan": lang_code,
            "ctp": 1
        }
        
        tts_response = requests.get(tts_url, params=tts_params)
        
        if tts_response.status_code != 200:
            raise Exception(f"百度TTS请求失败: {tts_response.status_code}")
        
        content_type = tts_response.headers.get('Content-Type', '')
        if 'audio' not in content_type:
            error_info = tts_response.json()
            raise Exception(f"百度TTS返回错误: {error_info}")
        
        with open(output_path, 'wb') as f:
            f.write(tts_response.content)
        
        return output_path
