import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Novel to Anime API"
    VERSION: str = "1.0.0"
    
    TTS_API_KEY: str = os.getenv("TTS_API_KEY", "")
    BAIDU_APP_ID: str = os.getenv("BAIDU_APP_ID", "")
    BAIDU_SECRET_KEY: str = os.getenv("BAIDU_SECRET_KEY", "")
    
    OUTPUT_DIR: str = "backend/output"
    
    class Config:
        case_sensitive = True

settings = Settings()
