from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskConfig(BaseModel):
    max_scene_length: int = 500
    image_provider: str = "stability"
    tts_provider: str = "azure"
    scene_duration: float = 5.0
    fps: int = 30


class TextTaskRequest(BaseModel):
    text: str
    config: Optional[TaskConfig] = None


class URLTaskRequest(BaseModel):
    url: str
    config: Optional[TaskConfig] = None


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: Optional[str] = None


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: int
    current_step: Optional[str] = None
    total_scenes: Optional[int] = None
    processed_scenes: Optional[int] = None
    error: Optional[str] = None


class TaskResultResponse(BaseModel):
    task_id: str
    status: TaskStatus
    video_url: Optional[str] = None
    scenes: Optional[List[Dict[str, Any]]] = None
    characters: Optional[List[str]] = None
    error: Optional[str] = None
