import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text, Float, JSON, Uuid
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agents = relationship("Agent", back_populates="owner")

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    domain = Column(Text, nullable=False)
    root_url = Column(Text, nullable=False)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_scraped = Column(DateTime)
    status = Column(String, default="pending")  # pending, scraping, ready, failed
    config = Column(JSON, default={})
    public_key = Column(String, unique=True, index=True)
    
    owner = relationship("User", back_populates="agents")
    scrape_jobs = relationship("ScrapeJob", back_populates="agent")
    chunks = relationship("Chunk", back_populates="agent")
    conversations = relationship("Conversation", back_populates="agent")
    faqs = relationship("FAQ", back_populates="agent")

class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(Uuid(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"))
    root_url = Column(Text, nullable=False)
    status = Column(String, default="queued")  # queued, running, completed, failed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    pages_scraped = Column(Integer, default=0)
    total_pages = Column(Integer)
    error_message = Column(Text)
    config = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent", back_populates="scrape_jobs")

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(Uuid(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"))
    chunk_id = Column(String, unique=True, nullable=False)  # Vector DB ID
    page_url = Column(Text, nullable=False)
    content = Column(Text)
    token_count = Column(Integer)
    metadata_ = Column("metadata", JSON, default={}) # metadata is reserved in SQLAlchemy sometimes, using metadata_ mapped to "metadata"
    importance_score = Column(Float, default=0.0)
    category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agent = relationship("Agent", back_populates="chunks")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(Uuid(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"))
    session_id = Column(String)
    query_text = Column(Text)
    query_audio_url = Column(Text)
    response_text = Column(Text)
    response_audio_url = Column(Text)
    sources = Column(JSON)
    latency_ms = Column(Integer)
    satisfaction_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent", back_populates="conversations")

class FAQ(Base):
    __tablename__ = "faqs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(Uuid(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    source_chunk_ids = Column(JSON)
    is_auto_generated = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agent = relationship("Agent", back_populates="faqs")

class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(Uuid(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"))
    metric_type = Column(String)
    metric_value = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
