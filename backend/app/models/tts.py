from pydantic import BaseModel, Field
from typing import Optional

class TTSRequest(BaseModel):
    text: str = Field(..., description="要转换为语音的文本内容", min_length=1, max_length=5000)
    provider: Optional[str] = Field("azure", description="TTS服务提供商: azure, openai, baidu")
    language: Optional[str] = Field("zh-CN", description="语言代码")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "这是一段测试文本，将被转换为语音。",
                "provider": "azure",
                "language": "zh-CN"
            }
        }

class TTSResponse(BaseModel):
    success: bool
    message: str
    audio_url: Optional[str] = None
    audio_filename: Optional[str] = None
