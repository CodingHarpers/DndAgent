import json
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from .agents import AgentFactory
from .tools import StorytellingTools

class AgentState(TypedDict):
    messages: List[BaseMessage]

class DungeonMasterOrchestrator:
    """
    Coordinates the narrative flow using a LangGraph state machine.
    """
    def __init__(self, memory_router=None, rules_lawyer=None):
        # 1. Setup Tools
        self.tool_factory = StorytellingTools(memory_router, rules_lawyer)
        self.tools = [
            self.tool_factory.retrieve_memory_tool(),
            self.tool_factory.adjudicate_rule_tool(),
            self.tool_factory.dice_roll_tool() # Added dice tool
        ]
        
        # 2. Setup Agent
        self.narrator_agent = AgentFactory.create_narrator(self.tools)

        # 3. Build Graph
        self.app = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # Define Nodes
        workflow.add_node("narrator", self._call_narrator)
        workflow.add_node("tools", ToolNode(self.tools))

        # Define Edges
        workflow.set_entry_point("narrator")

        # Conditional edge: If tools are called, go to 'tools', else END
        workflow.add_conditional_edges(
            "narrator",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )

        # From tools, go back to narrator to interpret results
        workflow.add_edge("tools", "narrator")

        return workflow.compile()

    def _call_narrator(self, state: AgentState):
        messages = state["messages"]
        response = self.narrator_agent.invoke({"messages": messages})
        return {"messages": [response]}

    def _should_continue(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the LLM wants to call a tool, it returns a tool_calls attribute
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        return "end"

    def process_turn(self, player_action: str, current_state: dict, history: List[BaseMessage] = None) -> Dict[str, Any]:
        """
        Process a single turn of the game.
        """
        if history is None:
            history = []
            
        # Format current state for the agent
        context_str = str(current_state.get("context", "No context provided"))
        location = current_state.get("location", "Unknown Location")
        module_context = current_state.get("module_context", "")
        phase = current_state.get("phase", "in_game")
        
        # Dynamic Prompt based on Phase
        if phase == "character_creation":
            system_instruction = (
                "GAME PHASE: CHARACTER CREATION\n"
                "You are the Dungeon Master. Your current goal is to help the player create their character.\n"
                "REQUIREMENTS:\n"
                "1. Ask the player to choose their CLASS (Fighter or Wizard). ONLY ask for Class.\n"
                "2. Do NOT ask for Race or Background at this time. Assume default Human if needed for narrative.\n"
                "3. Once the player has chosen a Class (Fighter/Wizard), you MUST include the tag [CHARACTER_COMPLETE] in your response.\n"
                "4. After [CHARACTER_COMPLETE], immediately transition to describing the setting (from the Module Context) and asking what they want to do.\n"
            )
        else:
            system_instruction = (
                "GAME PHASE: IN_GAME ADVENTURE\n"
                "You are the Dungeon Master. Narrate the story based on the Module Context and player actions.\n"
                "RULES:\n"
                "1. If the player attempts an action with a chance of failure (attacking, climbing, persuading), you MUST use the `roll_die` tool.\n"
                "2. After getting the die result, if you need to know if it succeeds according to strict rules, use `check_rule`.\n"
                "3. If you provided numbered options (1., 2..), interpret simple number inputs as selecting those options.\n"
                "4. Be robust to typos (e.g. 'file' -> 'fire').\n"
            )

        system_context = (
            f"{system_instruction}\n"
            f"Current State:\n"
            f"- Location: {location}\n"
            f"- Pre-retrieved Context: {context_str}\n"
            f"You may use tools to fetch MORE details or ROLL DICE if needed."
        )

        # 1. Construct messages
        # We start with existing history
        messages = list(history)
        
        # Add Module Context (Story + Maps) if available
        if module_context:
            messages.append(SystemMessage(content=module_context))

        # Add dynamic system context
        messages.append(SystemMessage(content=system_context))
        
        # Add player action
        messages.append(HumanMessage(content=player_action))
        
        # 2. Run the graph
        final_state = self.app.invoke({"messages": messages})
        
        # 3. Extract final response
        final_messages = final_state["messages"]
        last_message = final_messages[-1]
        narrative_text = last_message.content

        return {
            "narrative": narrative_text,
            "world_updates": {}, 
            "messages": final_messages
        }
