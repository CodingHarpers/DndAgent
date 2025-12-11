from typing import Dict, Any, List
import uuid
# LangGraph & LangChain imports
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
# App imports
from app.models.schemas import Scene, TurnResponse, PlayerStats
from app.agents.narrative_agent import NarrativeAgent
from app.agents.rules_lawyer_agent import RulesLawyerAgent
from app.agents.world_builder_agent import WorldBuilderAgent
from app.memory.router import MemoryRouter
from app.agents.tools import DndTools
from app.agents.state import AgentState
import uuid
from pydantic import BaseModel

class RuleCheckDecision(BaseModel):
    should_check: bool
    query: str
    reason: str
    
class DungeonMasterOrchestrator:
    """
    Orchestrates the game loop using a LangGraph state machine.
    
    This replaces the old imperative OrchestratorAgent. It manages:
    1. Tool execution (Buy, Sell, Attack) via the model's decision.
    2. Narrative generation via the NarrativeAgent (LLM).
    3. State updates to the Temporal Knowledge Graph (TKG).
    
    Graph Structure:
    [Narrator Node] --(calls tool?)--> [Tools Node] --(output)--> [Narrator Node]
           |
           +--(no tool)--> [END]
    """

    def __init__(self):
        # 1. Initialize Sub-Agents
        # NarrativeAgent will now be a graph node wrapper
        self.narrative_agent_wrapper = NarrativeAgent() 
        self.rules_agent = RulesLawyerAgent()
        self.world_agent = WorldBuilderAgent()
        self.memory_router = MemoryRouter()

        # 2. Setup Tools
        # We inject the TKG (from world_agent) into the tools factory
        self.tool_factory = DndTools(tkg=self.world_agent.tkg, rules_agent=self.rules_agent)
        self.tools = [
            self.tool_factory.get_buy_tool(),
            self.tool_factory.get_sell_tool(),
            self.tool_factory.get_attack_tool()
        ]
        
        # 3. Bind tools to the Narrative Agent's LLM
        # Note: NarrativeAgent needs a method to bind tools. We will add this.
        self.narrative_agent_wrapper.bind_tools(self.tools)

        # 4. Build the LangGraph
        self.app = self._build_graph()

    def _build_graph(self):
        """
        Constructs the StateGraph workflow.
        """
        workflow = StateGraph(AgentState)

        # -- Define Nodes --
        
        # Node 1: Narrator
        # The main LLM decision maker. It reviews history & context and produces either 
        # a narrative response OR a tool call request.
        workflow.add_node("narrator", self._call_narrator)
        
        # Node 2: Tools
        # A built-in LangGraph node that executes the function calls requested by the LLM.
        workflow.add_node("tools", ToolNode(self.tools))

        # -- Define Edges --
        
        workflow.set_entry_point("narrator")

        # Conditional Logic:
        # After specificing 'narrator', we check the output.
        # If the output has 'tool_calls', we route to 'tools'.
        # Otherwise, we route to END (turn complete).
        workflow.add_conditional_edges(
            "narrator",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )

        # After tools execute, we loop back to 'narrator' so it can describe the result
        # of the action (e.g., "You swung your sword and missed!").
        workflow.add_edge("tools", "narrator")

        return workflow.compile()

    def _call_narrator(self, state: AgentState):
        """
        Node function: Invokes the Narrative Agent.
        """
        print("[Orchestrator] Calling Narrator Node...")
        messages = state["messages"]
        # We delegate to the NarrativeAgent's invoke method
        response_msg = self.narrative_agent_wrapper.invoke(messages)
        # Return update to state (append new message)
        return {"messages": [response_msg]}

    def _should_continue(self, state: AgentState):
        """
        Edge function: Checks if the last message has tool calls.
        """
        messages = state["messages"]
        last_message = messages[-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            print(f"[Orchestrator] Tool Call Detected: {last_message.tool_calls}")
            return "continue"
        print("[Orchestrator] No tool call. Ending turn.")
        return "end"

    # -- Public API Methods (Matching old Orchestrator Interface) --

    def start_new_session(self) -> Scene:
        """
        Initializes a new game session.
        """
        session_id = str(uuid.uuid4())
        
        # Initialize Player in TKG
        initial_stats = {
            "hp_current": 20, "hp_max": 20, "gold": 50, "power": 12, "speed": 10
        }
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
        """
        Main entry point for handling a player turn.
        
        1. Fetches Context (Stats, Memory).
        2. Constructs Prompt/Messages.
        3. Runs the Graph.
        4. Returns the final narrative and updated state.
        """
        # 1. Fetch RPG State
        tkg = self.world_agent.tkg
        stats = tkg.get_player_stats(session_id)
        inventory = tkg.get_inventory(session_id)
        
        rpg_context = (
            f"\n[RPG STATE]\n"
            f"Health: {stats.get('hp_current')}/{stats.get('hp_max')}\n"
            f"Gold: {stats.get('gold')}\n"
            f"Inventory: {[i['name'] for i in inventory]}\n"
            f"Session ID: {session_id}" # Important for tools to know the session!
        )
        
        # 2. Retrieve Memory Context
        memory_context = self.memory_router.retrieve_context(player_input, session_id)
        
        # 3. Construct Input Messages
        # We can treat this as a fresh tailored prompt or append to a history if we were tracking it statefully.
        # Since this API is stateless per request (restoring session), we construct a robust system prompt.
        
        system_prompt = (
            "You are the Dungeon Master. Guide the player through the adventure.\n"
            "Use the provided tools to manage game state (Buying, Selling, Attacking).\n"
            "When calling a tool, ALWAYS pass the 'session_id' provided in the context.\n"
            f"{rpg_context}\n"
            f"Memory Context: {memory_context}\n"
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=player_input)
        ]
        
        # 4. Run Graph
        final_state = self.app.invoke({"messages": messages})
        
        # 5. Extract Result
        final_messages = final_state["messages"]
        last_message = final_messages[-1]
        narrative_text = last_message.content



            

    # # 3b. Standard Flow (if no tool executed)
    # if not new_scene:
    #     # Rules Adjudication Decision
    #     rule_check_system = (
    #         "You are the Game Master's PROACTIVE Rules Assistant.\n"
    #         "Your goal is to identify ANY opportunity where D&D 5e mechanics should influence the outcome. Don't just validate actions; look for bonuses, checks, and lore.\n\n"
    #         "### CHECK AGGRESSIVELY FOR THESE TRIGGERS:\n"
    #         "1. **Situational Awareness (Perception/Insight)**:\n"
    #         "   - Entering a new area? -> Check for Passive Perception (traps, hidden doors).\n"
    #         "   - Meeting an NPC? -> Check for Insight (detect lies).\n"
    #         "2. **Tactical Modifiers (Advantage/Disadvantage)**:\n"
    #         "   - Is the player Hiding? Flanking? In dim light? Prone?\n"
    #         "   - Ask Lawyer: 'Does attacking a Prone target give Advantage?'\n"
    #         "3. **Character Progression & Builds**:\n"
    #         "   - Did they ask about leveling up? -> Ask Lawyer: 'What features does a Fighter get at Level 3?'\n"
    #         "   - Did they ask about their Race? -> Ask Lawyer: 'What are the traits of a Tiefling?'\n"
    #         "4. **Action Validity & Mechanics**:\n"
    #         "   - Casting spells? -> Check Range, Components (V/S/M), Slots.\n"
    #         "   - Grappling/Shoving? -> Check Athletics vs Acrobatics rules.\n"
    #         "5. **Lore & Knowledge**:\n"
    #         "   - Inspecting a rune/monster? -> Check Arcana/Nature/History DC.\n\n"
    #         "Output JSON with:\n"
    #         "- should_check: bool\n"
    #         "- query: str (Formulate a specific question for the Rules Lawyer describing the exact state)\n"
    #         "- reason: str (Why is this check needed?)"
    #     )
        
    #     rule_check_user = (
    #         f"Current State: {rpg_context}\n"
    #         f"Player Input: \"{player_input}\"\n"
    #         "Identify any necessary rule checks, passive scores, or tactical advantages."
    #     )
        
    #     decision = generation_client.generate_structured(rule_check_system, rule_check_user, RuleCheckDecision)
    #     print(f"Rule Check Decision: {decision}")
    #     if decision and decision.should_check:
    #         print(f"[Orchestrator] Rule Check Triggered: {decision.query} (Reason: {decision.reason})")
    #         rule_result = self.rules_agent.adjudicate(decision.query, context)
    #     else:
    #         rule_result = None # No rule check needed
        
    #     new_scene = self.narrative_agent.generate_scene(
    #         player_input, 
    #         context, 
    #         rule_result
    #     )
        
    #     # World Update for standard narrative
    #     if new_scene:
    #         self.world_agent.update_world(new_scene)
        

        try:
            current_stats = PlayerStats(**tkg.get_player_stats(session_id))
        except:
            current_stats = None

        # Note: 'scene' object usually contains more metadata. 
        # For this refactor, we wrap the text in a Scene object.
        new_scene = Scene(
            scene_id=session_id,
            title="Adventure Continues",
            narrative_text=narrative_text,
            location="Unknown", # Ideally extracted from state
            characters_present=[],
            available_actions=[],
            metadata={"session_id": session_id}
        )

        # 6. Update World State (Async in production, sync here for MVP)
        # Verify that we actually want to update the world with this narrative
        self.world_agent.update_world(new_scene)

        return TurnResponse(
            scene=new_scene,
            rule_outcome=None, # Handled implicitly by tools now
            player_stats=current_stats,
            action_log=None
        )
