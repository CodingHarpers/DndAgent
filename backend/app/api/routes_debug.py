from fastapi import APIRouter
from typing import List, Dict
from app.models.schemas import MemoryRecord

router = APIRouter()

@router.get("/session/{session_id}/memory")
async def get_session_memory(session_id: str) -> List[Dict]:
    """Retrieves episodic memory for a given session."""
    # Placeholder: In real logic, query EpisodicStore
    return [{"summary": "Mock memory", "timestamp": "2023-01-01T12:00:00"}]

@router.get("/session/{session_id}/world_state")
async def get_world_state(session_id: str) -> Dict:
    """Retrieves current world state (TKG facts)."""
    # Placeholder
    return {"location": "Dungeon", "factions": ["Goblins"]}
