from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import PlayerInput, TurnResponse, Scene, RuleAdjudicationResult, BuyRequest
from app.agents.orchestrator import DungeonMasterOrchestrator
# Dependency injection handled here in a real app

router = APIRouter()

# Singleton instance for demo purposes
# In prod, manage lifecycle properly
orchestrator = DungeonMasterOrchestrator()

@router.post("/start_session", response_model=Scene)
async def start_session():
    """Initializes a new game session."""
    initial_scene = orchestrator.start_new_session()
    print(f"DEBUG: start_session returning: {initial_scene}")
    return initial_scene

@router.post("/step", response_model=TurnResponse)
async def stepped_turn(input_data: PlayerInput):
    """Takes player input and advances the game state."""
    response = orchestrator.process_turn(input_data.text, input_data.session_id)
    return response

@router.post("/buy")
async def buy_item(request: BuyRequest):
    # Short-circuit: check orchestrator -> world_agent -> tkg
    # For now, instantiate a fresh TKG or use singleton if available.
    from app.memory.semantic_tkg import SemanticTKG
    tkg = SemanticTKG()
    try:
        result = tkg.purchase_item(request.session_id, request.item_id)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        return result
    finally:
        tkg.close()

@router.get("/inventory/{session_id}")
async def get_inventory(session_id: str):
    from app.memory.semantic_tkg import SemanticTKG
    tkg = SemanticTKG()
    try:
        return tkg.get_inventory(session_id)
    finally:
        tkg.close()

@router.get("/stats/{session_id}")
async def get_stats(session_id: str):
    from app.memory.semantic_tkg import SemanticTKG
    tkg = SemanticTKG()
    try:
        return tkg.get_player_stats(session_id)
    finally:
        tkg.close()
