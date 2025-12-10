from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Acorn"
    DATABASE_URL: str = "sqlite:///./demo.db"
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Gemini
    GEMINI_API_KEY: Optional[str] = None
    
    # ElevenLabs
    ELEVENLABS_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()
