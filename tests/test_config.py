from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from unittest.mock import patch, MagicMock

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_config.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from app.models.models import Agent, User, ScrapeJob # Import models to register them with Base
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
        json={"root_url": "https://example.com", "email": "config_test@example.com", "name": "Config Test Agent"}
    )
    return response.json()["id"]

@patch("app.main.run_scraper_task")
def test_update_config(mock_task):
    agent_id = _onboard_helper()
    
    # Test PATCH config
    new_config = {
        "voice_id": "test_voice_id",
        "personality": "You are a test bot."
    }
    response = client.patch(f"/v1/agents/{agent_id}/config", json=new_config)
    assert response.status_code == 200
    data = response.json()
    assert data["config"]["voice_id"] == "test_voice_id"
    assert data["config"]["personality"] == "You are a test bot."
    
    # Verify persistence by fetching status (which doesn't return config but ensures no error)
    # Ideally we'd have a GET /agent endpoint, but we can check via DB or just trust the PATCH response for now
    # Let's try to query and see if it mocks correctly with the new config

@patch("app.main.run_scraper_task")
@patch("app.services.rag.RAGService.search")
@patch("app.services.rag.RAGService.generate_answer_stream")
@patch("app.services.voice.VoiceService.generate_audio")
def test_query_uses_config(mock_audio, mock_stream, mock_search, mock_task):
    agent_id = _onboard_helper()
    
    # Update config
    client.patch(f"/v1/agents/{agent_id}/config", json={
        "voice_id": "custom_voice",
        "personality": "Custom instruction"
    })
    
    # Mock RAG responses
    mock_search.return_value = []
    
    async def async_gen(*args, **kwargs):
        yield "Test response"
    mock_stream.return_value = async_gen()
    
    # Mock Audio response to return a string (base64)
    mock_audio.return_value = "dGVzdF9hdWRpbw=="
    
    # Query
    response = client.post(f"/v1/agents/{agent_id}/query", json={"query": "Hello"})
    assert response.status_code == 200
    
    # Verify generate_answer_stream was called with custom instruction
    # Note: We need to check the call args. 
    # Since it's an async generator called in the endpoint, we might need to inspect the mock carefully.
    # However, checking if the endpoint runs without error is a good first step.
    
    # Verify VoiceService was called with custom voice_id
    # The endpoint consumes the stream and calls voice.generate_audio
    # We need to ensure the stream consumption happens. TestClient handles StreamingResponse by iterating it.
    
    # Force consumption of stream
    list(response.iter_lines())
    
    # Check if generate_audio was called with voice_id="custom_voice"
    # mock_audio.assert_called_with("Test response", voice_id="custom_voice") 
    # Note: The actual call might be slightly different depending on buffering, but "Test response" is short enough.
    # Let's just check if it was called.
    assert mock_audio.called
    call_kwargs = mock_audio.call_args.kwargs
    assert call_kwargs.get("voice_id") == "custom_voice"
