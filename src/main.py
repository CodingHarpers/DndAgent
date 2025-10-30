import json
import sys
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
        self.storyteller = DungeonMasterOrchestrator(
            memory_router=self.memory, 
            rules_lawyer=self.rules_lawyer
        )
        self.chat_history: List[BaseMessage] = []

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
            current_state={**current_state, "context": context, "rule_outcome": rule_check},
            history=self.chat_history
        )
        
        # Update history
        # We need to filter out the duplicate SystemMessages we injected transiently.
        # But 'process_turn' returns the FULL list used in that execution?
        # My process_turn implementation returns `final_state["messages"]`.
        # LangGraph appends new messages.
        
        # The input messages were [History] + [SystemContext] + [Human].
        # The output messages are [History] + [SystemContext] + [Human] + [AIMessage] (+ ToolMessages).
        
        # We want to persist [Human] + [AIMessage] (+ ToolMessages) into self.chat_history.
        # And we want to discard [SystemContext].
        
        # Let's see:
        new_messages = narrative_response["messages"]
        
        # We know the start of the list matches our input history.
        # We can just take the slice from len(self.chat_history) onwards.
        
        delta_messages = new_messages[len(self.chat_history):]
        
        # Filter out the SystemMessage we added (it was the first one in the delta)
        filtered_delta = []
        for m in delta_messages:
            # We assume the only SystemMessage in delta is the one we added at index 0 of delta.
            # But let's be safe.
            if isinstance(m, SystemMessage) and "Current State" in str(m.content):
                continue
            filtered_delta.append(m)
            
        self.chat_history.extend(filtered_delta)
        
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
    system = ArcanaSystem()
    
    # Mock initial state
    current_state = {"location": "Dark Dungeon", "hp": 20}
    
    print("\n=== Welcome to A.R.C.A.N.A. ===")
    print("Initializing game session...\n")
    
    # Initial Prompt to start the game
    # We pretend the user said "Start Game" to kick off the intro
    initial_response = system.game_loop("Start Game. Please introduce the setting and ask me to create a character.", current_state)
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
