from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.routes import tts, generate, tasks, websocket

app = FastAPI(
    title="Novel to Anime API",
    description="API for converting text to speech and generating anime videos from novels",
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

app.include_router(tts.router, prefix="/api", tags=["Text-to-Speech"])
app.include_router(generate.router, prefix="/api", tags=["Generate"])
app.include_router(tasks.router, prefix="/api", tags=["Tasks"])
app.include_router(websocket.router, prefix="/api", tags=["WebSocket"])

@app.get("/")
async def root():
    return {
        "message": "Novel to Anime API",
        "version": "1.0.0",
        "endpoints": {
            "tts": "/api/tts",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
