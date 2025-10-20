import json
from src.storytelling.orchestrator import DungeonMasterOrchestrator
from src.memory.router import MemoryRouter
from src.rulerag.lawyer import RulesLawyer

class ArcanaSystem:
    """
    Main system class that integrates Storytelling, Memory, and RuleRAG modules.
    """
    def __init__(self):
        # Initialize sub-systems
        # In a real scenario, we would pass actual DB connections here
        self.memory = MemoryRouter(vector_store=None, graph_store=None)
        self.rules_lawyer = RulesLawyer()
        self.storyteller = DungeonMasterOrchestrator()

    def game_loop(self, player_input: str, current_state: dict):
        """
        Main game loop that merges logic from all agents.
        """
        print(f"[*] Processing Player Action: {player_input}")

        # 1. Retrieve Context (Memory Module)
        # Fetch relevant past events (episodic) and world facts (semantic)
        context = self.memory.retrieve_context(player_input)
        print(f"[*] Memory Context Retrieved: {context}")

        # 2. Adjudicate Rules (RuleRAG Module)
        # Determine if the action needs a dice roll or rule check
        # For simplicity, we assume a dummy rule check here
        rule_check = self.rules_lawyer.adjudicate(
            action_intent=player_input, 
            rule_json={"difficulty_class": 10, "success_outcome": "Action succeeds"}, 
            die_roll=15 # Mock roll
        )
        print(f"[*] Rule Adjudication: {rule_check}")

        # 3. Generate Narrative (Storytelling Module)
        # The orchestrator uses the context and rule outcome to generate the story
        narrative_response = self.storyteller.process_turn(
            player_action=player_input,
            current_state={**current_state, "context": context, "rule_outcome": rule_check}
        )
        
        # 4. Merge Logic (Merging narrative "Fluff" with game "Crunch")
        # Combine the creative output with the strict rule outcome
        final_output = self._merge_outputs(narrative_response, rule_check, context)
        
        return final_output

    def _merge_outputs(self, narrative, rule_result, context):
        """
        Merges the narrative description with the mechanical game state changes.
        """
        merged_result = {
            "narrative": narrative.get("narrative", "The dungeon is silent."),
            "game_state_update": {
                "outcome": rule_result.get("outcome"),
                "effect": rule_result.get("effect"),
                "relevant_memory": context
            },
            "meta": {
                "status": "turn_complete"
            }
        }
        return merged_result

if __name__ == "__main__":
    # Example usage
    system = ArcanaSystem()
    
    # Mock initial state
    initial_state = {"location": "Dark Dungeon", "hp": 20}
    
    # Run a turn
    response = system.game_loop("I attack the goblin with my sword", initial_state)
    
    print("\n--- Final Merged Output ---")
    print(json.dumps(response, indent=2))
