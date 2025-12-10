from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class AgentCreate(BaseModel):
    root_url: HttpUrl

class AgentUpdate(BaseModel):
    voice_id: Optional[str] = None
    personality: Optional[str] = None

class AgentResponse(BaseModel):
    id: UUID
    root_url: str
    status: str
    public_key: Optional[str] = None
    config: Optional[Dict[str, Any]] = {}
    
    class Config:
        from_attributes = True

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []
    audio_base64: Optional[str] = None

class ScrapeStatus(BaseModel):
    status: str
    pages_scraped: int
    total_pages: Optional[int] = None
    logs: List[Dict[str, Any]] = []
