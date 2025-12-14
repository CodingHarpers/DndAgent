from typing import Dict, Any, List, Optional
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
from app.models.schemas import Scene, TurnResponse, PlayerStats, RuleAdjudicationResult
from app.agents.narrative_agent import NarrativeAgent
from app.agents.rules_lawyer_agent import RulesLawyerAgent
from app.agents.world_builder_agent import WorldBuilderAgent
from app.memory.router import MemoryRouter
from app.agents.tools import DndTools
from app.agents.state import AgentState


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
            self.tool_factory.get_create_character_tool(),
            self.tool_factory.get_check_rules_tool(),
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

    def _get_previous_narrative_text(self, history: List[BaseMessage]) -> str:
        """
        Returns the most recent DM narrative text (last AIMessage content) from the stored history.
        """
        for m in reversed(history):
            if isinstance(m, AIMessage) and m.content:
                # Gemini/LangChain can represent message content as str or a richer structure.
                # We only want the textual narrative here.
                if isinstance(m.content, str):
                    return m.content
                return str(m.content)
        return ""

    def _extract_check_rules_result(self, messages: List[BaseMessage]) -> Optional[str]:
        """
        Extract the latest check_rules tool result (rule_result string) from the message list.
        """
        last_payload: Any = None
        for m in messages:
            if isinstance(m, ToolMessage) and getattr(m, "name", None) == "check_rules":
                last_payload = m.content

        if last_payload is None:
            return None

        # ToolMessage.content can be a dict or a JSON-ish string depending on runtime serialization.
        if isinstance(last_payload, dict):
            return last_payload.get("rule_result")

        if isinstance(last_payload, str):
            try:
                parsed = json.loads(last_payload)
                if isinstance(parsed, dict):
                    return parsed.get("rule_result")
            except Exception:
                return None

        return None

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
        
        tool_calls = getattr(last_message, "tool_calls", None)
        if tool_calls:
            print(f"[Orchestrator] Tool Call Detected: {tool_calls}")
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
        # Seed history with the initial DM output so "previous_narrative_text" is available on turn 1.
        self.session_histories[session_id] = [AIMessage(content=initial_scene.narrative_text)]
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
        previous_narrative_text = self._get_previous_narrative_text(history)

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
                "\n"
                "IMPORTANT (Rules): Before responding with any narrative, you MUST call `check_rules` exactly once "
                "to proactively identify any D&D 5e mechanics that should apply.\n"
                f"Module Content: {self.module_content}\n"
            )
        else:
            system_instruction = (
    "You are the **Dungeon Master (DM)**. Your primary role is to guide the player through an immersive D&D 5e adventure.\n"
    f"Module Content: {self.module_content}\n"
    "\n"
    "### THE GOLDEN RULE: \"ADJUDICATE FIRST, NARRATE SECOND\"\n"
    "You possess a `check_rules` tool, which is your link to the **Rules Lawyer Engine**.\n"
    "Before you generate ANY narrative response, you must act as a **Silent Referee** and evaluate the current state.\n"
    "DO NOT rely on your own training data for mechanics. If there is even a 1% chance a mechanic applies, CONSULT THE LAWYER.\n"
    "\n"
    "### WHEN TO CALL `check_rules` (Triggers)\n"
    "Be AGGRESSIVE. If the player breathes wrong, check if there's a rule for it. Look for these specific disputes:\n"
    "1. **Validation Disputes**: Player says \"I attack/cast/jump\". -> *Lawyer:* \"Is the target in range? Do they have line of sight? Is the spell slot available?\"\n"
    "2. **State Conflicts**: Player is Prone/Grappled/Blinded. -> *Lawyer:* \"How does being Prone affect this attack roll?\"\n"
    "3. **Passive Awareness**: Player enters a room. -> *Lawyer:* \"What is the Passive Perception threshold for the trap here?\"\n"
    "4. **Build & Progression**: Player levels up or uses a racial trait. -> *Lawyer:* \"What exact features does a Level 3 Fighter gain?\"\n"
    "5. **Lore & DC**: Player inspects a rune. -> *Lawyer:* \"What is the History DC to recognize this symbol?\"\n"
    "\n"
    "### PROTOCOL FOR CALLING THE TOOL\n"
    "When calling `check_rules`, construct your `query` as a **specific adjudication request**:\n"
    "  - BAD: \"Check stealth rules.\"\n"
    "  - GOOD: \"Player (Rogue) wants to Hide behind a barrel while observed by a Guard. Is this allowed, and what is the Stealth check DC vs Passive Perception?\"\n"
    "\n"
    "### NARRATION INSTRUCTIONS\n"
    "Once you receive the tool output (RuleAdjudication):\n"
    "1. **Enforce the Verdict**: If Action Failed, you narrate the failure. Do not fudge the dice unless necessary for plot.\n"
    "2. **Weave the Mechanics**: Don't just say \"You take 5 damage.\" Say \"The goblin's scimitar finds a gap in your armor (AC 15), slashing for 5 slashing damage.\"\n"
)

        system_prompt = (
            f"{system_instruction}\n"
            "When calling a tool, ALWAYS pass the 'session_id' provided in the context.\n"
            "When calling `check_rules`, ALWAYS pass:\n"
            "- session_id\n"
            "- query (your concrete rules question)\n"
            "- reason (why you need this rule check)\n"
            "- player_input (the user's latest message)\n"
            "- previous_narrative_text (the LAST DM output shown below)\n"
            "- memory_context (the memory context shown below)\n"
            f"{rpg_context}\n"
            f"Memory Context: {memory_context}\n"
            f"Previous Narrative Text (last DM output): {previous_narrative_text}\n"
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

        # 6. Rule adjudication now runs via the `check_rules` tool (invoked by the LLM before narrating).
        rule_explanation = self._extract_check_rules_result(final_messages)
        rule_result = RuleAdjudicationResult(explanation=rule_explanation) if rule_explanation else None

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
                # "rule_result": rule_result,
                "narrative_text": narrative_text,
            }
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"[Orchestrator] Logged turn {round_number} to: {log_path}")
        except Exception as e:
            # Logging should never break gameplay; fail silently except for debug print.
            print(f"[Orchestrator] Failed to write conversation log: {e}")
