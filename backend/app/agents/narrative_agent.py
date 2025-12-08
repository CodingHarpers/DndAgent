from app.models.schemas import Scene, RuleAdjudicationResult
from app.services.llm_client import llm_client
from typing import Dict, Any

class NarrativeAgent:
    def generate_scene(self, player_input: str, context: Dict, rule_result: RuleAdjudicationResult) -> Scene:
        # Construct prompt
        system_prompt = "You are a D&D Dungeon Master. Generate the next scene based on player input and rule outcomes."
        user_prompt = f"Player: {player_input}\nRules: {rule_result}\nContext: {context}"
        
        # Call LLM
        print(f"[NarrativeAgent] Generating scene for input: {player_input}...")
        try:
            scene = llm_client.generate_structured(
                system_prompt, 
                user_prompt, 
                Scene
            )
            print("[NarrativeAgent] Generation successful.")
        except Exception as e:
            print(f"[NarrativeAgent] Generation failed: {e}")
            scene = None
        
        if not scene:
            # Fallback if LLM fails
            return Scene(
                scene_id="error_id",
                title="The Mists of Confusion",
                narrative_text="The Dungeon Master seems distracted (LLM Error). Please try again.",
                location="Void",
                characters_present=[],
                available_actions=["Retry"]
            )
        
        return scene
