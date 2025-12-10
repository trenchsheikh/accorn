from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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

from unittest.mock import patch

@patch("app.main.run_scraper_task")
def test_onboard(mock_task):
    _onboard_helper()

def _onboard_helper():
    response = client.post(
        "/v1/onboard",
        json={"root_url": "https://example.com", "email": "test@example.com", "name": "Test Agent"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["root_url"] == "https://example.com/"
    assert "id" in data
    return data["id"]

@patch("app.main.run_scraper_task")
def test_status(mock_task):
    agent_id = _onboard_helper()
    response = client.get(f"/v1/agents/{agent_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["queued", "running", "completed", "failed"]

@patch("app.main.run_scraper_task")
def test_query(mock_task):
    agent_id = _onboard_helper()
    response = client.post(
        f"/v1/agents/{agent_id}/query",
        json={"query": "Hello"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
