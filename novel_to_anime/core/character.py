import re
from typing import Dict, List, Set


class CharacterManager:
    def __init__(self):
        self.characters: Dict[str, Dict] = {}
        self.character_appearances: Dict[str, int] = {}
    
    def extract_characters(self, text: str) -> Set[str]:
        chinese_name_pattern = r'[李王张刘陈杨赵黄周吴徐孙胡朱高林何郭马罗梁宋郑谢韩唐冯于董萧程曹袁邓许傅沈曾彭吕苏卢蒋蔡贾丁魏薛叶阎余潘杜戴夏钟汪田任姜范方石姚谭廖邹熊金陆郝孔白崔康毛邱秦江史顾侯邵孟龙万段漕钱汤尹黎易常武乔贺赖龚文][一-龥]{1,2}'
        
        english_name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        
        chinese_names = set(re.findall(chinese_name_pattern, text))
        english_names = set(re.findall(english_name_pattern, text))
        
        all_names = chinese_names.union(english_names)
        
        valid_names = set()
        for name in all_names:
            if len(name) >= 2 and not self._is_common_word(name):
                valid_names.add(name)
        
        return valid_names
    
    def _is_common_word(self, word: str) -> bool:
        common_words = {
            '这个', '那个', '什么', '怎么', '为什么', '可以', '不是',
            '没有', '已经', '应该', '可能', '时候', '地方', '东西',
            '事情', '问题', '办法', '方法', '结果', '原因'
        }
        return word in common_words
    
    def register_character(self, name: str, description: str = None):
        if name not in self.characters:
            self.characters[name] = {
                'name': name,
                'description': description or f"角色{name}",
                'appearance_count': 0,
                'visual_prompt': self._generate_visual_prompt(name, description)
            }
            self.character_appearances[name] = 0
    
    def _generate_visual_prompt(self, name: str, description: str = None) -> str:
        base_prompt = f"character named {name}"
        
        if description:
            base_prompt += f", {description}"
        else:
            hash_val = sum(ord(c) for c in name) % 10
            
            styles = [
                "young person with short black hair and determined eyes",
                "middle-aged person with glasses and professional attire",
                "elderly person with white hair and gentle expression",
                "young person with long hair and casual clothing",
                "athletic person with sporty outfit",
                "elegant person with formal attire",
                "mysterious person with dark clothing",
                "cheerful person with bright colored clothes",
                "serious person in business suit",
                "artistic person with creative style"
            ]
            base_prompt += f", {styles[hash_val]}"
        
        return base_prompt
    
    def update_character_appearance(self, name: str):
        if name in self.characters:
            self.characters[name]['appearance_count'] += 1
            self.character_appearances[name] += 1
    
    def get_character_prompt(self, name: str) -> str:
        if name in self.characters:
            return self.characters[name]['visual_prompt']
        return ""
    
    def get_scene_characters(self, scene_text: str) -> List[str]:
        found_characters = []
        for name in self.characters.keys():
            if name in scene_text:
                found_characters.append(name)
                self.update_character_appearance(name)
        return found_characters
    
    def enhance_scene_prompt(self, scene_prompt: str, scene_text: str) -> str:
        characters = self.get_scene_characters(scene_text)
        
        if characters:
            character_descriptions = []
            for char_name in characters:
                char_prompt = self.get_character_prompt(char_name)
                if char_prompt:
                    character_descriptions.append(char_prompt)
            
            if character_descriptions:
                enhanced_prompt = f"{scene_prompt}, featuring: {', '.join(character_descriptions)}"
                return enhanced_prompt
        
        return scene_prompt
    
    def get_character_summary(self) -> Dict:
        return {
            'total_characters': len(self.characters),
            'characters': [
                {
                    'name': char['name'],
                    'appearances': char['appearance_count'],
                    'visual_prompt': char['visual_prompt']
                }
                for char in self.characters.values()
            ]
        }
