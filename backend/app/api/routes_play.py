from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import PlayerInput, TurnResponse, Scene, RuleAdjudicationResult
from app.agents.orchestrator import OrchestratorAgent
# Dependency injection handled here in a real app

router = APIRouter()

# Singleton instance for demo purposes
# In prod, manage lifecycle properly
orchestrator = OrchestratorAgent()

@router.post("/start_session")
async def start_session():
    """Initializes a new game session."""
    initial_scene = orchestrator.start_new_session()
    return {"scene": initial_scene}

@router.post("/step", response_model=TurnResponse)
async def stepped_turn(input_data: PlayerInput):
    """Takes player input and advances the game state."""
    response = orchestrator.process_turn(input_data.text, input_data.session_id)
    return response
