import uuid
import json
from pathlib import Path
from typing import Dict, Optional
from app.models.task import TaskStatus, TaskStatusResponse


class TaskService:
    def __init__(self):
        self.tasks_dir = Path("tasks")
        self.tasks_dir.mkdir(exist_ok=True)
    
    def create_task(self, task_type: str, data: Dict) -> str:
        task_id = str(uuid.uuid4())
        
        task_data = {
            "task_id": task_id,
            "type": task_type,
            "status": TaskStatus.PENDING,
            "progress": 0,
            "data": data
        }
        
        task_file = self.tasks_dir / f"{task_id}.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_data, f, ensure_ascii=False, indent=2)
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatusResponse]:
        task_file = self.tasks_dir / f"{task_id}.json"
        
        if not task_file.exists():
            return None
        
        with open(task_file, 'r', encoding='utf-8') as f:
            task_data = json.load(f)
        
        return TaskStatusResponse(
            task_id=task_id,
            status=task_data.get("status", TaskStatus.PENDING),
            progress=task_data.get("progress", 0),
            current_step=task_data.get("current_step"),
            total_scenes=task_data.get("total_scenes"),
            processed_scenes=task_data.get("processed_scenes"),
            error=task_data.get("error")
        )
    
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: int = 0,
        current_step: str = None,
        total_scenes: int = None,
        processed_scenes: int = None,
        video_path: str = None,
        error: str = None
    ):
        task_file = self.tasks_dir / f"{task_id}.json"
        
        if not task_file.exists():
            return
        
        with open(task_file, 'r', encoding='utf-8') as f:
            task_data = json.load(f)
        
        task_data["status"] = status
        task_data["progress"] = progress
        if current_step:
            task_data["current_step"] = current_step
        if total_scenes is not None:
            task_data["total_scenes"] = total_scenes
        if processed_scenes is not None:
            task_data["processed_scenes"] = processed_scenes
        if video_path:
            task_data["video_path"] = video_path
        if error:
            task_data["error"] = error
        
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_data, f, ensure_ascii=False, indent=2)
    
    def get_task_result(self, task_id: str) -> Optional[Dict]:
        task_file = self.tasks_dir / f"{task_id}.json"
        
        if not task_file.exists():
            return None
        
        with open(task_file, 'r', encoding='utf-8') as f:
            return json.load(f)
