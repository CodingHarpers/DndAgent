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
        
        # Initialize Player in TKG
        initial_stats = {
            "hp_current": 20, "hp_max": 20, "gold": 50, "power": 12, "speed": 10
        }
        # We need access to TKG here. Assuming WorldBuilderAgent has it, or we can instantiate directly.
        # But cleaner to access via a dedicated or shared instance.
        # For now, let's reach into world_agent's tkg since it is already there.
        self.world_agent.tkg.create_player(session_id, "Traveler", initial_stats)

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
        # 0. Fetch RPG State (Stats & Inventory)
        tkg = self.world_agent.tkg
        stats = tkg.get_player_stats(session_id)
        inventory = tkg.get_inventory(session_id)
        
        # 1. Retrieve Context
        # Inject RPG state into context so NarrativeAgent sees it
        rpg_context = f"\n[RPG STATE]\nHealth: {stats.get('hp_current')}/{stats.get('hp_max')}\nGold: {stats.get('gold')}\nInventory: {[i['name'] for i in inventory]}"
        
        context = self.memory_router.retrieve_context(player_input, session_id)
        context['rpg_state'] = rpg_context # Add to context dict
        
        # 2. Intent Detection & Tool Execution
        # We check if the user wants to perform a tool-supported action (Buy/Sell)
        from app.services.generation import generation_client
        from app.agents.tools import dnd_tools

        system_prompt = (
            "You are an AI assistant for a D&D game. Your job is to DETECT INTENT and call the appropriate tool.\n"
            "If the player wants to BUY something, you MUST call 'buy_item'.\n"
            "If the player wants to SELL something, you MUST call 'sell_item'.\n"
            "Do NOT narrate. Do NOT generate text. ONLY call the tool if applicable.\n"
            "If no tool applies, output 'NO_TOOL'."
        )
        user_prompt = f"Player Input: {player_input}\nContext: {rpg_context}"
        
        tool_response = generation_client.generate_with_tools(system_prompt, user_prompt, dnd_tools)
        
        new_scene = None
        rule_result = None

        # Check for function call
        try:
            # Gemini Python SDK structure for function calls
            # It might appear in candidates[0].content.parts[0].function_call
            if tool_response and tool_response.candidates:
                part = tool_response.candidates[0].content.parts[0]
                if part.function_call:
                    fc = part.function_call
                    tool_name = fc.name
                    args = fc.args
                    
                    print(f"[Orchestrator] Tool Call Detected: {tool_name} with {args}")
                    
                    action_result = None
                    if tool_name == "buy_item":
                        item_id = args.get("item_id")
                        action_result = tkg.purchase_item(session_id, item_id)
                    elif tool_name == "sell_item":
                        item_id = args.get("item_id")
                        action_result = tkg.sell_item(session_id, item_id)
                        
                    if action_result:
                        # 3a. Narration of Tool Outcome
                        new_scene = self.narrative_agent.generate_outcome_narration(action_result)
        except Exception as e:
            print(f"[Orchestrator] Tool processing error: {e}")

        # 3b. Standard Flow (if no tool executed)
        if not new_scene:
            # Rules Adjudication
            rule_result = self.rules_agent.adjudicate(player_input, context)
            
            new_scene = self.narrative_agent.generate_scene(
                player_input, 
                context, 
                rule_result
            )
            
            # World Update for standard narrative
            if new_scene:
                self.world_agent.update_world(new_scene)
        
        # 4. Return Response with fresh stats
        from app.models.schemas import PlayerStats
        try:
            current_stats = PlayerStats(**tkg.get_player_stats(session_id))
        except:
            current_stats = None

        return TurnResponse(
            scene=new_scene,
            rule_outcome=rule_result,
            player_stats=current_stats
        )
