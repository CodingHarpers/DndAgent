import json
import sys
import os
from typing import List
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage, HumanMessage

from src.storytelling.orchestrator import DungeonMasterOrchestrator
from src.memory.router import MemoryRouter
from src.rulerag.lawyer import RulesLawyer

class ArcanaSystem:
    """
    Main system class that integrates Storytelling, Memory, and RuleRAG modules.
    """
    def __init__(self):
        # Initialize sub-systems
        self.memory = MemoryRouter(vector_store=None, graph_store=None)
        self.rules_lawyer = RulesLawyer()
        
        # Load Module Context
        self.module_context = self._load_module_context()
        
        self.storyteller = DungeonMasterOrchestrator(
            memory_router=self.memory, 
            rules_lawyer=self.rules_lawyer
        )
        self.chat_history: List[BaseMessage] = []

    def _load_module_context(self) -> str:
        """
        Loads the adventure module text and map references.
        """
        try:
            with open("data/story/hallows_end.txt", "r") as f:
                story_text = f.read()
        except FileNotFoundError:
            story_text = "No module loaded."

        # List maps
        map_files = []
        map_dir = "data/story/Map Files"
        if os.path.exists(map_dir):
            map_files = os.listdir(map_dir)
        
        map_info = "\n".join([f"- {m}" for m in map_files])
        
        return (
            f"ADVENTURE MODULE: Hallow's End\n"
            f"AVAILABLE MAPS (in {map_dir}):\n{map_info}\n\n"
            f"MODULE CONTENT:\n{story_text}\n"
        )

    def game_loop(self, player_input: str, current_state: dict):
        """
        Main game loop that merges logic from all agents.
        """
        print(f"[*] Processing Player Action: {player_input}")

        # 1. Retrieve Context (Memory Module)
        # Fetch relevant past events (episodic) and world facts (semantic)
        context = self.memory.retrieve_context(player_input)
        
        # 2. Adjudicate Rules (RuleRAG Module)
        rule_check = self.rules_lawyer.adjudicate(
            action_intent=player_input, 
            rule_json={"difficulty_class": 10, "success_outcome": "Action succeeds"}, 
            die_roll=15 # Mock roll
        )

        # 3. Generate Narrative (Storytelling Module)
        # Inject Module Context into the current state or history for this turn
        narrative_response = self.storyteller.process_turn(
            player_action=player_input,
            current_state={
                **current_state, 
                "context": context, 
                "rule_outcome": rule_check,
                "module_context": self.module_context # Pass this to orchestrator
            },
            history=self.chat_history
        )
        
        # Update history logic...
        new_messages = narrative_response["messages"]
        delta_messages = new_messages[len(self.chat_history):]
        
        filtered_delta = []
        for m in delta_messages:
            # Filter out SystemMessages that are just context injections
            if isinstance(m, SystemMessage):
                continue
            filtered_delta.append(m)
            
        self.chat_history.extend(filtered_delta)
        
        # 4. Merge Logic
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
    system = ArcanaSystem()
    
    # Mock initial state
    current_state = {"location": "Outside Novegrad", "hp": 20}
    
    print("\n=== Welcome to A.R.C.A.N.A. ===")
    print("Initializing game session...\n")
    
    # Initial Prompt to start the game
    initial_response = system.game_loop(
        "Start Game. Use the loaded Adventure Module 'Hallow's End'. "
        "Introduce the setting based on the module's 'Outside the Walls' section. "
        "Then ask me to create a character.", 
        current_state
    )
    print(f"\nDM: {initial_response['narrative']}\n")
    
    while True:
        try:
            user_input = input(">> You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting game...")
                break
                
            response = system.game_loop(user_input, current_state)
            print(f"\nDM: {response['narrative']}\n")
            
        except KeyboardInterrupt:
            print("\nExiting game...")
            break
