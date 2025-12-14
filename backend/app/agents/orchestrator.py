from typing import Dict, Any, List
import uuid
import os
import json

# LangGraph & LangChain imports
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)
# App imports
from app.models.schemas import Scene, TurnResponse, PlayerStats
from app.agents.narrative_agent import NarrativeAgent
from app.agents.rules_lawyer_agent import RulesLawyerAgent
from app.agents.world_builder_agent import WorldBuilderAgent
from app.memory.router import MemoryRouter
from app.agents.tools import DndTools
from app.agents.state import AgentState
from app.services.generation import generation_client
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
            self.tool_factory.get_attack_tool(),
            self.tool_factory.get_create_character_tool()
        ]
        
        # 3. Bind tools to the Narrative Agent's LLM
        # Note: NarrativeAgent needs a method to bind tools. We will add this.
        self.narrative_agent_wrapper.bind_tools(self.tools)

        # 4. Load Module
        try:
            with open("data/story/hallows_end.txt", "r") as f:
                self.module_content = f.read()
        except FileNotFoundError:
            try:
                with open("../data/story/hallows_end.txt", "r") as f:
                    self.module_content = f.read()
            except:
                self.module_content = "Welcome to the adventure."

        # 5. Build the LangGraph
        self.app = self._build_graph()

        # 6. In-memory session history storage
        self.session_histories: Dict[str, List[BaseMessage]] = {}
        # 7. Per-session round counter (1, 2, 3...) for structured logging / analytics
        self.session_round_numbers: Dict[str, int] = {}

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
        # Initialize round counter for this session
        self.session_round_numbers[session_id] = 0
        
        # Initialize Player in TKG
        initial_stats = {
            "hp_current": 20, "hp_max": 20, "gold": 50, "power": 12, "speed": 10
        }
        self.world_agent.tkg.create_player(session_id, "Traveler", initial_stats)
        # Reset character details for new session
        self.world_agent.tkg.update_player_profile(session_id, "Traveler", "Unknown", "Unknown")

        initial_scene = Scene(
            scene_id=session_id,
            title="The Beginning",
            narrative_text=f"{self.module_content}\n\nBefore we begin, please tell me: What is your Name, Race, and Class?",
            location="Hallow's End",
            characters_present=[],
            available_actions=["Create Character"],
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
        # Round counter (monotonic per session)
        round_number = self.session_round_numbers.get(session_id, 0) + 1
        self.session_round_numbers[session_id] = round_number

        # 1. Fetch RPG State
        tkg = self.world_agent.tkg
        stats = tkg.get_player_stats(session_id)
        inventory = tkg.get_inventory(session_id)
        
        rpg_context = (
            f"\n[RPG STATE]\n"
            f"Health: {stats.get('hp_current')}/{stats.get('hp_max')}\n"
            f"Gold: {stats.get('gold')}\n"
            f"Inventory: {[i['name'] for i in inventory]}\n"
            f"Session ID: {session_id}"  # Important for tools to know the session!
        )
        
        # 2. Retrieve Memory Context
        memory_context = self.memory_router.retrieve_context(player_input, session_id)
        
        # 3. Construct Input Messages
        # Retrieve session history
        history = self.session_histories.get(session_id, [])

        # Check Character Creation Status
        player_race = stats.get('race')
        player_class = stats.get('class')
        
        if not player_race or not player_class or player_race == "Unknown" or player_class == "Unknown":
            system_instruction = (
                "GAME PHASE: CHARACTER CREATION\n"
                "You are the Dungeon Master. The player needs to create their character.\n"
                "The player should provide Name, Race, and Class.\n"
                "Extract these details and use the `create_character` tool to save them.\n"
                "If information is missing, ask for it.\n"
                "Once the tool is successfully called, transition to the game intro.\n"
                f"Module Content: {self.module_content}\n"
            )
        else:
            system_instruction = (
                "You are the Dungeon Master. Guide the player through the adventure.\n"
                f"Module Content: {self.module_content}\n"
                "Use the provided tools to manage game state (Buying, Selling, Attacking).\n"
            )

        system_prompt = (
            f"{system_instruction}\n"
            "When calling a tool, ALWAYS pass the 'session_id' provided in the context.\n"
            f"{rpg_context}\n"
            f"Memory Context: {memory_context}\n"
        )
        
        # We assume the SystemMessage is always fresh context and shouldn't be accumulated in history
        # History contains [Human, AI, Human, AI...]
        messages = [SystemMessage(content=system_prompt)] + history + [HumanMessage(content=player_input)]
        
        # 4. Run Graph
        final_state = self.app.invoke({"messages": messages})
        
        # 5. Extract Result & Update History
        final_messages = final_state["messages"]
        
        # Update history: Filter out the initial SystemMessage and store the rest
        # This preserves the full conversation flow including tool calls
        new_history = [m for m in final_messages if not isinstance(m, SystemMessage)]
        self.session_histories[session_id] = new_history

        last_message = final_messages[-1]
        narrative_text = last_message.content

        # 6. Proactive rules adjudication when no explicit tool was executed
        # Detect whether any tool message was used during this graph run.
        tools_executed = any(isinstance(m, ToolMessage) for m in final_messages)

        rule_result = None
        if not tools_executed:
            # Rules Adjudication Decision (ported from legacy orchestrator flow)
            rule_check_system = (
                "You are the Game Master's PROACTIVE Rules Assistant.\n"
                "Your goal is to identify ANY opportunity where D&D 5e mechanics should influence the outcome. Don't just validate actions; look for bonuses, checks, and lore.\n\n"
                "### CHECK AGGRESSIVELY FOR THESE TRIGGERS:\n"
                "1. **Situational Awareness (Perception/Insight)**:\n"
                "   - Entering a new area? -> Check for Passive Perception (traps, hidden doors).\n"
                "   - Meeting an NPC? -> Check for Insight (detect lies).\n"
                "2. **Tactical Modifiers (Advantage/Disadvantage)**:\n"
                "   - Is the player Hiding? Flanking? In dim light? Prone?\n"
                "   - Ask Lawyer: 'Does attacking a Prone target give Advantage?'\n"
                "3. **Character Progression & Builds**:\n"
                "   - Did they ask about leveling up? -> Ask Lawyer: 'What features does a Fighter get at Level 3?'\n"
                "   - Did they ask about their Race? -> Ask Lawyer: 'What are the traits of a Tiefling?'\n"
                "4. **Action Validity & Mechanics**:\n"
                "   - Casting spells? -> Check Range, Components (V/S/M), Slots.\n"
                "   - Grappling/Shoving? -> Check Athletics vs Acrobatics rules.\n"
                "5. **Lore & Knowledge**:\n"
                "   - Inspecting a rune/monster? -> Check Arcana/Nature/History DC.\n\n"
                "Output JSON with:\n"
                "- should_check: bool\n"
                "- query: str (Formulate a specific question for the Rules Lawyer describing the exact state)\n"
                "- reason: str (Why is this check needed?)"
            )

            rule_check_user = (
                f"Current State: {rpg_context}\n"
                f"Player Input: \"{player_input}\"\n"
                f"Final Narrative: \"{narrative_text}\"\n"
                "Identify any necessary rule checks, passive scores, or tactical advantages."
            )

            decision = generation_client.generate_structured(
                rule_check_system, rule_check_user, RuleCheckDecision
            )
            print(f"Rule Check Decision: {decision}")

            if decision and decision.should_check:
                print(
                    f"[Orchestrator] Rule Check Triggered: {decision.query} "
                    f"(Reason: {decision.reason})"
                )
                context: Dict[str, Any] = {
                    "rpg_state": rpg_context,
                    "memory_context": memory_context,
                    "player_input": player_input,
                    "narrative_text": narrative_text,
                    "session_id": session_id,
                }
                rule_result = self.rules_agent.adjudicate(decision.query, context)

        # Persist structured JSON log for this turn (after we know rule_result)
        self._log_conversation(
            session_id=session_id,
            round_number=round_number,
            player_input=player_input,
            rule_result=(rule_result.explanation if rule_result else None),
            narrative_text=narrative_text,
        )

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
            location="Unknown",  # Ideally extracted from state
            characters_present=[],
            available_actions=[],
            metadata={"session_id": session_id}
        )

        # 7. Update World State (Async in production, sync here for MVP)
        # Verify that we actually want to update the world with this narrative
        self.world_agent.update_world(new_scene)

        return TurnResponse(
            scene=new_scene,
            rule_outcome=rule_result,
            player_stats=current_stats,
            action_log=None
        )

    def _log_conversation(
        self,
        session_id: str,
        round_number: int,
        player_input: str,
        rule_result: str | None,
        narrative_text: str,
    ) -> None:
        """
        Append the current turn's data to a JSONL log file (one JSON object per line).

        Logs are stored under a local 'logs' directory, one file per session.
        Intentionally excludes timestamps to make downstream processing stable/reproducible.
        """
        try:
            # Ensure logs directory exists (relative to backend working dir)
            logs_dir = "data/logs"
            os.makedirs(logs_dir, exist_ok=True)

            log_path = os.path.join(logs_dir, f"{session_id}.jsonl")
            record = {
                "round_number": round_number,
                "session_id": session_id,
                "player_input": player_input,
                "rule_result": rule_result,
                "narrative_text": narrative_text,
            }
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"[Orchestrator] Logged turn {round_number} to: {log_path}")
        except Exception as e:
            # Logging should never break gameplay; fail silently except for debug print.
            print(f"[Orchestrator] Failed to write conversation log: {e}")
