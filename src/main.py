import json
import sys
import os
from enum import Enum
from typing import List, Optional, Dict
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage, HumanMessage

from src.storytelling.orchestrator import DungeonMasterOrchestrator
from src.memory.router import MemoryRouter
from src.rulerag.lawyer import RulesLawyer

class GamePhase(str, Enum):
    CHARACTER_CREATION = "character_creation"
    IN_GAME = "in_game"

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
        
        # State Management
        self.phase = GamePhase.CHARACTER_CREATION
        self.character_sheet: Dict[str, Optional[str]] = {
            "class": None
        }

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
        # 1. Retrieve Context (Memory Module)
        context = self.memory.retrieve_context(player_input)
        
        # NOTE: We REMOVED the pre-emptive RulesLawyer check here.
        # Now the Orchestrator/Agent decides when to roll dice or check rules.

        # 2. Generate Narrative (Storytelling Module)
        narrative_response = self.storyteller.process_turn(
            player_action=player_input,
            current_state={
                **current_state, 
                "context": context, 
                "module_context": self.module_context,
                "phase": self.phase,
                "character_sheet": self.character_sheet
            },
            history=self.chat_history
        )
        
        # 3. Check for Phase Transition Signal from Agent
        ai_text = narrative_response["narrative"]
        if "[CHARACTER_COMPLETE]" in ai_text:
            self.phase = GamePhase.IN_GAME
            ai_text = ai_text.replace("[CHARACTER_COMPLETE]", "").strip()
            narrative_response["narrative"] = ai_text

        # Update history logic...
        new_messages = narrative_response["messages"]
        delta_messages = new_messages[len(self.chat_history):]
        
        filtered_delta = []
        for m in delta_messages:
            if isinstance(m, SystemMessage):
                continue
            filtered_delta.append(m)
            
        self.chat_history.extend(filtered_delta)
        
        return {
            "narrative": ai_text, # Return the cleaned text
            "meta": {
                "status": "turn_complete"
            }
        }

if __name__ == "__main__":
    system = ArcanaSystem()
    
    # Mock initial state
    current_state = {"location": "Outside Novegrad", "hp": 20}
    
    print("\n=== Welcome to A.R.C.A.N.A. ===")
    print("Initializing game session...\n")
    
    # Initial Prompt to start the game
    # We instruct the system to start character creation
    initial_response = system.game_loop(
        "Start Game. Use the loaded Adventure Module 'Hallow's End'. "
        "Begin by asking me to choose my Class.", 
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
