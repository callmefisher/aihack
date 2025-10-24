from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import tts

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

app.include_router(tts.router, prefix="/api", tags=["Text-to-Speech"])

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
