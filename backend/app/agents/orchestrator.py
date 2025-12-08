from typing import Dict, Any
from app.models.schemas import Scene, TurnResponse, RuleAdjudicationResult
from app.agents.narrative_agent import NarrativeAgent
from app.agents.rules_lawyer_agent import RulesLawyerAgent
from app.agents.world_builder_agent import WorldBuilderAgent
from app.memory.router import MemoryRouter
import uuid

class OrchestratorAgent:
    def __init__(self):
        self.narrative_agent = NarrativeAgent()
        self.rules_agent = RulesLawyerAgent()
        self.world_agent = WorldBuilderAgent()
        self.memory_router = MemoryRouter()

    def start_new_session(self) -> Scene:
        # Initial Setup
        session_id = str(uuid.uuid4())
        initial_scene = Scene(
            scene_id=session_id,
            title="The Beginning",
            narrative_text="You stand at the entrance of a dark dungeon. The air is cold and damp.",
            location="Dungeon Entrance",
            characters_present=[],
            available_actions=["Enter the dungeon", "Look around"],
            metadata={"session_id": session_id}
        )
        return initial_scene

    def process_turn(self, player_input: str, session_id: str) -> TurnResponse:
        # 1. Retrieve Context
        context = self.memory_router.retrieve_context(player_input, session_id)
        
        # 2. Rules Adjudication
        rule_result = self.rules_agent.adjudicate(player_input, context)
        
        # 3. World Update (if needed)
        # In a full impl, this would update TKG based on outcome
        
        # 4. Generate Narrative
        # Combine context, rule outcome, and player input
        new_scene = self.narrative_agent.generate_scene(
            player_input, 
            context, 
            rule_result
        )
        
        return TurnResponse(
            scene=new_scene,
            rule_outcome=rule_result
        )
