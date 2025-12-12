# backend/app/core/config.py

import os
from typing import List
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # System Configuration
    ENV_MODE: str = "development"
    ENABLE_EVALUATION: bool = True
    LOG_LEVEL: str = "INFO"
    MAX_INPUT_LENGTH: int = 1000

    # Security
    PATIENT_ID_SALT: str = "changeme_random_salt_string"

    # Models (NVIDIA NIM)
    NVIDIA_LLM_API_KEY: str
    NVIDIA_EMBEDDING_API_KEY: str
    LLM_MODEL_NAME: str = "nvidia/llama-3.3-nemotron-super-49b-v1.5"
    EMBEDDING_MODEL_NAME: str = "nvidia/nv-embedqa-e5-v5"
    LLM_API_URL: str = "https://integrate.api.nvidia.com/v1"

    # Database Configuration
    WEAVIATE_URL: str = "http://localhost:8080"
    RUN_SYNC_ON_STARTUP: bool = False
    
    # Logging
    LOG_FILE_PATH: str = "logs/system.log"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore" # Allow extra fields in .env without error

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()