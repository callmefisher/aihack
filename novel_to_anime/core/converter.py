import os
import json
from typing import Dict
from pathlib import Path

from .parser import NovelParser
from .character import CharacterManager
from ..generators.image import ImageGenerator
from ..generators.audio import TextToSpeech
from ..video.composer import VideoComposer


class NovelToAnimeConverter:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        self.parser = NovelParser(
            max_scene_length=self.config.get('max_scene_length', 500)
        )
        
        self.character_manager = CharacterManager()
        
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
        
        print("\n👥 提取角色信息...")
        all_characters = self.character_manager.extract_characters(novel_text)
        print(f"   发现 {len(all_characters)} 个角色: {', '.join(list(all_characters)[:10])}")
        
        for character in all_characters:
            self.character_manager.register_character(character)
        
        print("\n🎨 生成场景图片...")
        for i, scene in enumerate(scenes):
            print(f"   生成场景 {i+1}/{len(scenes)}...")
            
            base_prompt = scene['narration'][:500]
            enhanced_prompt = self.character_manager.enhance_scene_prompt(
                base_prompt, 
                scene['text']
            )
            
            image_path = os.path.join(output_dir, f"scene_{i+1:03d}.png")
            
            try:
                scene['image_path'] = self.image_gen.generate_image(enhanced_prompt, image_path)
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
        
        character_summary_path = os.path.join(output_dir, "characters.json")
        with open(character_summary_path, 'w', encoding='utf-8') as f:
            json.dump(
                self.character_manager.get_character_summary(),
                f,
                ensure_ascii=False,
                indent=2
            )
        print(f"   角色信息已保存到: {character_summary_path}")
        
        try:
            result = self.video_composer.create_video(scenes, video_path)
            print(f"\n✅ 视频生成完成: {result}")
            return result
        except Exception as e:
            print(f"\n❌ 视频合成失败: {e}")
            raise
