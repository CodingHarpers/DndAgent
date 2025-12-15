from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import pytest
import sys
import os

# Add the backend to path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))

# Mock the orchestrator before importing the app/routes
# We need to mock the MODULE where orchestrator is instantiated or the CLASS itself
# Since routes_play.py instantiates it at module level, we should patch where it is import/used

@pytest.fixture
def mock_orchestrator():
    with patch("app.api.routes_play.orchestrator") as mock:
        yield mock

@pytest.fixture
def client():
    # Lazy import to allow mocking to take effect if we were doing it earlier, 
    # but here we rely on the mock_orchestrator fixture being active during tests
    from app.main import app 
    return TestClient(app)

def test_start_session(client, mock_orchestrator):
    # Setup mock return value
    mock_scene = {
        "scene_id": "test-session-123",
        "title": "Test Title",
        "narrative_text": "Welcome to the test adventure.",
        "location": "Test Location",
        "characters_present": [],
        "available_actions": ["Test Action"],
        "metadata": {}
    }
    # The API expects a Pydantic model response, but in the implementation 
    # orchestrator.start_new_session returns a Scene object which FastAPI serializes.
    # We can have the mock return a dict if FastAPI validation allows, or a mock object.
    # Let's verify what the route returns.
    
    mock_orchestrator.start_new_session.return_value = mock_scene

    response = client.post("/api/play/start_session")
    
    assert response.status_code == 200
    data = response.json()
    assert data["scene_id"] == "test-session-123"
    assert "narrative_text" in data
    mock_orchestrator.start_new_session.assert_called_once()


def test_step(client, mock_orchestrator):
    # Setup mock return value for process_turn
    mock_turn_response = {
        "scene": {
            "scene_id": "test-session-123",
            "title": "Next Scene",
            "narrative_text": "You move forward.",
            "location": "Hallway",
            "characters_present": [],
            "available_actions": [],
            "metadata": {}
        },
        "rule_outcome": None,
        "player_stats": None,
        "action_log": None
    }
    mock_orchestrator.process_turn.return_value = mock_turn_response

    payload = {
        "session_id": "test-session-123",
        "text": "I walk down the hallway."
    }
    response = client.post("/api/play/step", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["scene"]["narrative_text"] == "You move forward."
    mock_orchestrator.process_turn.assert_called_once_with("I walk down the hallway.", "test-session-123")
