import re
from typing import List, Dict


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
