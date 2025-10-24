#!/usr/bin/env python3
import os
import json
import re
from typing import List, Dict
from pathlib import Path


class NovelParser:
    def __init__(self, max_scene_length: int = 500):
        self.max_scene_length = max_scene_length
    
    def parse_novel(self, novel_text: str) -> List[Dict]:
        scenes = []
        paragraphs = [p.strip() for p in novel_text.split('\n\n') if p.strip()]
        
        current_scene = {
            'text': '',
            'narration': '',
            'dialogue': []
        }
        
        for paragraph in paragraphs:
            if len(current_scene['text']) + len(paragraph) > self.max_scene_length:
                if current_scene['text']:
                    scenes.append(current_scene.copy())
                current_scene = {
                    'text': paragraph,
                    'narration': self._extract_narration(paragraph),
                    'dialogue': self._extract_dialogue(paragraph)
                }
            else:
                current_scene['text'] += '\n' + paragraph
                current_scene['narration'] += '\n' + self._extract_narration(paragraph)
                current_scene['dialogue'].extend(self._extract_dialogue(paragraph))
        
        if current_scene['text']:
            scenes.append(current_scene)
        
        return scenes
    
    def _extract_narration(self, text: str) -> str:
        narration = re.sub(r'["""](.*?)["""]', '', text)
        narration = re.sub(r'"(.*?)"', '', narration)
        return narration.strip()
    
    def _extract_dialogue(self, text: str) -> List[str]:
        dialogues = []
        dialogues.extend(re.findall(r'["""](.*?)["""]', text))
        dialogues.extend(re.findall(r'"(.*?)"', text))
        return dialogues


class ImageGenerator:
    def __init__(self, api_key: str = None, provider: str = "stability"):
        self.api_key = api_key or os.getenv('IMAGE_API_KEY')
        self.provider = provider
    
    def generate_image(self, prompt: str, output_path: str) -> str:
        if not self.api_key:
            print(f"⚠️ 警告: 未配置API密钥，将生成占位符图片")
            return self._generate_placeholder(output_path, prompt)
        
        if self.provider == "stability":
            return self._generate_stability_ai(prompt, output_path)
        elif self.provider == "openai":
            return self._generate_openai_dalle(prompt, output_path)
        else:
            raise ValueError(f"不支持的图像生成器: {self.provider}")
    
    def _generate_placeholder(self, output_path: str, prompt: str) -> str:
        from PIL import Image, ImageDraw, ImageFont
        
        img = Image.new('RGB', (1024, 576), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        
        text = f"场景描述:\n{prompt[:100]}..."
        d.text((50, 250), text, fill=(255, 255, 255))
        
        img.save(output_path)
        return output_path
    
    def _generate_stability_ai(self, prompt: str, output_path: str) -> str:
        import requests
        
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        body = {
            "text_prompts": [
                {
                    "text": f"anime style, high quality, {prompt}",
                    "weight": 1
                }
            ],
            "cfg_scale": 7,
            "height": 576,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }
        
        response = requests.post(url, headers=headers, json=body)
        
        if response.status_code == 200:
            data = response.json()
            import base64
            with open(output_path, 'wb') as f:
                f.write(base64.b64decode(data['artifacts'][0]['base64']))
            return output_path
        else:
            raise Exception(f"图像生成失败: {response.text}")
    
    def _generate_openai_dalle(self, prompt: str, output_path: str) -> str:
        import openai
        
        openai.api_key = self.api_key
        
        response = openai.Image.create(
            prompt=f"anime style, high quality illustration: {prompt}",
            n=1,
            size="1024x1024"
        )
        
        image_url = response['data'][0]['url']
        
        import requests
        img_data = requests.get(image_url).content
        with open(output_path, 'wb') as f:
            f.write(img_data)
        
        return output_path


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


class VideoComposer:
    def __init__(self):
        pass
    
    def create_video(
        self,
        scenes: List[Dict],
        output_path: str,
        fps: int = 30,
        scene_duration: float = 5.0
    ) -> str:
        from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, TextClip
        
        clips = []
        
        for i, scene in enumerate(scenes):
            image_path = scene.get('image_path')
            audio_path = scene.get('audio_path')
            text = scene.get('text', '')
            
            if not image_path or not os.path.exists(image_path):
                print(f"⚠️ 场景 {i+1} 的图片不存在: {image_path}")
                continue
            
            img_clip = ImageClip(image_path)
            
            if audio_path and os.path.exists(audio_path):
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration
                img_clip = img_clip.set_duration(duration)
                img_clip = img_clip.set_audio(audio_clip)
            else:
                img_clip = img_clip.set_duration(scene_duration)
            
            if text:
                txt_clip = TextClip(
                    text[:100] + '...' if len(text) > 100 else text,
                    fontsize=24,
                    color='white',
                    bg_color='black',
                    size=(img_clip.w * 0.9, None),
                    method='caption'
                )
                txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(img_clip.duration)
                img_clip = CompositeVideoClip([img_clip, txt_clip])
            
            clips.append(img_clip)
        
        if not clips:
            raise Exception("没有有效的场景可以合成视频")
        
        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac')
        
        return output_path


class NovelToAnimeConverter:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        self.parser = NovelParser(
            max_scene_length=self.config.get('max_scene_length', 500)
        )
        
        self.image_gen = ImageGenerator(
            api_key=self.config.get('image_api_key'),
            provider=self.config.get('image_provider', 'stability')
        )
        
        self.tts = TextToSpeech(
            api_key=self.config.get('tts_api_key'),
            provider=self.config.get('tts_provider', 'azure')
        )
        
        self.video_composer = VideoComposer()
    
    def convert(
        self,
        novel_path: str,
        output_dir: str = "output",
        video_name: str = "anime.mp4"
    ) -> str:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        print("📖 读取小说文本...")
        with open(novel_path, 'r', encoding='utf-8') as f:
            novel_text = f.read()
        
        print("🔍 解析小说场景...")
        scenes = self.parser.parse_novel(novel_text)
        print(f"   发现 {len(scenes)} 个场景")
        
        print("\n🎨 生成场景图片...")
        for i, scene in enumerate(scenes):
            print(f"   生成场景 {i+1}/{len(scenes)}...")
            
            image_prompt = scene['narration'][:500]
            image_path = os.path.join(output_dir, f"scene_{i+1:03d}.png")
            
            try:
                scene['image_path'] = self.image_gen.generate_image(image_prompt, image_path)
            except Exception as e:
                print(f"      ⚠️ 图片生成失败: {e}")
                scene['image_path'] = None
        
        print("\n🎤 生成语音旁白...")
        for i, scene in enumerate(scenes):
            print(f"   生成场景 {i+1}/{len(scenes)} 的语音...")
            
            audio_text = scene['text'][:1000]
            audio_path = os.path.join(output_dir, f"scene_{i+1:03d}.mp3")
            
            try:
                scene['audio_path'] = self.tts.generate_speech(audio_text, audio_path)
            except Exception as e:
                print(f"      ⚠️ 语音生成失败: {e}")
                scene['audio_path'] = None
        
        print("\n🎬 合成最终视频...")
        video_path = os.path.join(output_dir, video_name)
        
        scenes_metadata_path = os.path.join(output_dir, "scenes_metadata.json")
        with open(scenes_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(scenes, f, ensure_ascii=False, indent=2)
        
        try:
            result = self.video_composer.create_video(scenes, video_path)
            print(f"\n✅ 视频生成完成: {result}")
            return result
        except Exception as e:
            print(f"\n❌ 视频合成失败: {e}")
            raise


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='将小说转换为动漫视频')
    parser.add_argument('novel', help='小说文本文件路径')
    parser.add_argument('-o', '--output', default='output', help='输出目录')
    parser.add_argument('-n', '--name', default='anime.mp4', help='输出视频文件名')
    parser.add_argument('-c', '--config', help='配置文件路径 (JSON格式)')
    
    args = parser.parse_args()
    
    config = {}
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    converter = NovelToAnimeConverter(config)
    
    try:
        result = converter.convert(args.novel, args.output, args.name)
        print(f"\n🎉 转换成功! 视频已保存到: {result}")
    except Exception as e:
        print(f"\n❌ 转换失败: {e}")
        exit(1)


if __name__ == "__main__":
    main()
