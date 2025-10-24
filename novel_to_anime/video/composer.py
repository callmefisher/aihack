import os
from typing import List, Dict


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
