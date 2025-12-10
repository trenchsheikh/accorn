from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, get_db
from app.models.models import Agent, User, ScrapeJob
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from unittest.mock import patch, MagicMock

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_admin.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def _onboard_helper():
    response = client.post(
        "/v1/onboard",
        json={"root_url": "https://example.com", "email": "admin_test@example.com", "name": "Admin Test Agent"}
    )
    return response.json()["id"]

@patch("app.main.run_scraper_task")
@patch("app.services.rag.RAGService.search") # Mock search to avoid real DB calls in RAG init if any
@patch("google.generativeai.GenerativeModel.generate_content")
@patch("app.services.voice.VoiceService.generate_audio")
def test_admin_intent(mock_audio, mock_generate, mock_search, mock_task):
    agent_id = _onboard_helper()
    
    # Mock Gemini response for intent parsing
    mock_response = MagicMock()
    mock_response.text = '{"reply": "Here are the voices.", "show_voice_options": true}'
    mock_generate.return_value = mock_response
    
    # Mock Audio generation
    mock_audio.return_value = "dGVzdF9hdWRpbw=="
    
    # Test Intent Endpoint with voice request
    response = client.post("/v1/admin/intent", json={
        "text": "Show me voices",
        "agent_id": agent_id
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Here are the voices."
    assert data["voice_options"] is not None
    assert len(data["voice_options"]) > 0
    assert data["voice_options"][0]["name"] == "Bella (American, Soft)"

@patch("app.services.voice.VoiceService.generate_audio")
def test_speak_endpoint(mock_audio):
    mock_audio.return_value = "cHJldmlld19hdWRpbw=="
    
    response = client.post("/v1/admin/speak", json={
        "text": "Hello",
        "voice_id": "test_id"
    })
    
    assert response.status_code == 200
    assert response.json()["audio_base64"] == "cHJldmlld19hdWRpbw=="
    mock_audio.assert_called_with("Hello", voice_id="test_id")
