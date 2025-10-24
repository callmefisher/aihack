from fastapi import APIRouter, HTTPException, BackgroundTasks
from pathlib import Path
import json

from app.models.task import (
    TextTaskRequest,
    URLTaskRequest,
    TaskResponse,
    TaskStatusResponse,
    TaskResultResponse,
    TaskStatus
)
from app.services.task_service import TaskService
from app.services.converter_service import ConverterService
from app.services.url_fetcher import URLFetcher

router = APIRouter()
task_service = TaskService()
converter_service = ConverterService(task_service)
url_fetcher = URLFetcher()


@router.post("/tasks/text", response_model=TaskResponse)
async def create_text_task(
    request: TextTaskRequest,
    background_tasks: BackgroundTasks
):
    config_dict = request.config.dict() if request.config else {}
    
    task_id = task_service.create_task("text", {
        "text": request.text,
        "config": config_dict
    })
    
    background_tasks.add_task(
        converter_service.process_text_task,
        task_id,
        request.text,
        config_dict
    )
    
    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        message="任务已创建，正在处理中"
    )


@router.post("/tasks/url", response_model=TaskResponse)
async def create_url_task(
    request: URLTaskRequest,
    background_tasks: BackgroundTasks
):
    try:
        text = url_fetcher.fetch_text_from_url(request.url)
        
        if not text or len(text) < 100:
            raise HTTPException(
                status_code=400,
                detail="无法从URL提取有效内容"
            )
        
        config_dict = request.config.dict() if request.config else {}
        
        task_id = task_service.create_task("url", {
            "url": request.url,
            "text": text,
            "config": config_dict
        })
        
        background_tasks.add_task(
            converter_service.process_text_task,
            task_id,
            text,
            config_dict
        )
        
        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="任务已创建，正在处理中"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    status = task_service.get_task_status(task_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return status


@router.get("/tasks/{task_id}/result", response_model=TaskResultResponse)
async def get_task_result(task_id: str):
    result = task_service.get_task_result(task_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    output_dir = Path(f"output/{task_id}")
    
    scenes = None
    characters = None
    
    scenes_file = output_dir / "scenes_metadata.json"
    if scenes_file.exists():
        with open(scenes_file, 'r', encoding='utf-8') as f:
            scenes = json.load(f)
    
    characters_file = output_dir / "characters.json"
    if characters_file.exists():
        with open(characters_file, 'r', encoding='utf-8') as f:
            char_data = json.load(f)
            characters = list(char_data.get('characters', {}).keys())
    
    return TaskResultResponse(
        task_id=task_id,
        status=result.get("status", TaskStatus.PENDING),
        video_url=result.get("video_path"),
        scenes=scenes,
        characters=characters,
        error=result.get("error")
    )
