import os
import sys
from pathlib import Path
from typing import Dict, Callable, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from novel_to_anime import NovelToAnimeConverter
from app.models.task import TaskStatus
from app.services.task_service import TaskService


class ConverterService:
    def __init__(self, task_service: TaskService):
        self.task_service = task_service
    
    def process_text_task(
        self,
        task_id: str,
        text: str,
        config: Dict
    ):
        try:
            self.task_service.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                progress=0,
                current_step="初始化转换器"
            )
            
            converter = NovelToAnimeConverter(config)
            output_dir = f"output/{task_id}"
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            temp_novel_path = f"{output_dir}/input.txt"
            with open(temp_novel_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            self.task_service.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                progress=10,
                current_step="解析文本"
            )
            
            video_name = f"{task_id}.mp4"
            video_path = converter.convert(temp_novel_path, output_dir, video_name)
            
            relative_video_path = f"/output/{task_id}/{video_name}"
            
            self.task_service.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                progress=100,
                current_step="完成",
                video_path=relative_video_path
            )
            
        except Exception as e:
            self.task_service.update_task_status(
                task_id,
                TaskStatus.FAILED,
                progress=0,
                error=str(e)
            )
