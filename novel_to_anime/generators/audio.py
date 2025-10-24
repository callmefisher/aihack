import os


class TextToSpeech:
    def __init__(self, api_key: str = None, provider: str = "azure"):
        self.api_key = api_key or os.getenv('TTS_API_KEY')
        self.provider = provider
    
    def generate_speech(self, text: str, output_path: str, language: str = "zh-CN") -> str:
        if not self.api_key:
            print(f"⚠️ 警告: 未配置TTS API密钥，将生成静音音频")
            return self._generate_silence(output_path, duration=len(text) * 0.2)
        
        if self.provider == "azure":
            return self._generate_azure_tts(text, output_path, language)
        elif self.provider == "openai":
            return self._generate_openai_tts(text, output_path)
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
