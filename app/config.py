"""
Avia ML Service — Configuration
"""
from typing import Optional

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    avia_backend_url: str = "https://aiva-backend-tnp0.onrender.com"
    ml_service_port: int = 8100
    ml_service_host: str = "0.0.0.0"
    openai_api_key: Optional[str] = None
    huggingface_api_token: Optional[str] = None
    huggingface_summary_model: str = "Falconsai/medical_summarization"
    face_model: str = "small"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
