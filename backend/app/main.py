from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.routes import tasks

app = FastAPI(
    title="Novel to Anime API",
    description="将小说转换为动漫视频的 Web API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

output_dir = Path("output")
output_dir.mkdir(exist_ok=True)
app.mount("/output", StaticFiles(directory="output"), name="output")

app.include_router(tasks.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Novel to Anime API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
