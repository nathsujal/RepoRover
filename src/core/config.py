"""
Configuration settings for RepoRover.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    """Application settings using pydantic-settings."""
    
    # Application settings
    APP_NAME: str = "RepoRover"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    REPOSITORIES_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "repositories")
    KNOWLEDGE_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "knowledge")
    MEMORY_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "memory")
    
    # API settings
    API_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Memory settings
    VECTOR_STORE_PATH: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "vector_store")
    EPISODIC_MEMORY_DB_URL: str = Field(default_factory=lambda: f"sqlite:///{(Path(__file__).parent.parent.parent / 'data' / 'memory' / 'episodic_memory.db').absolute()}")
    
    # Agent settings
    DEFAULT_AGENT_TIMEOUT: int = 300  # 5 minutes
    MAX_CONCURRENT_AGENTS: int = 5
    
    # Rate limiting
    RATE_LIMIT: str = "100/minute"
    
    # Gemini API Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Query Planner Configuration
    QUERY_MAX_CONTEXT_LENGTH: int = 8000
    QUERY_MAX_PLAN_STEPS: int = 10
    QUERY_DEFAULT_SEARCH_LIMIT: int = 10
    
    # DSPy Configuration
    DSPY_CACHE_DIR: Path = Path("./cache/dspy")
    DSPY_LOG_LEVEL: str = "INFO"

    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)


# Create a singleton instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.REPOSITORIES_DIR, exist_ok=True)
os.makedirs(settings.KNOWLEDGE_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
os.makedirs(settings.MEMORY_DIR, exist_ok=True)
