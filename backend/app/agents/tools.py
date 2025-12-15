from typing import Dict, Any, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field

class CheckRulesInput(BaseModel):
    """Input for the check_rules tool."""
    
    query: str = Field(
        ..., 
        description=(
            "A specific, context-rich question describing the game state to adjudicate. "
            "MUST include relevant entities, conditions, and intent. "
            "Example: 'Level 3 Rogue with 12 Dex wants to hide behind a barrel in dim light while a Guard is watching. Is this allowed and what is the DC?'"
        )
    )
    
    reason: str = Field(
        ..., 
        description=(
            "The specific trigger category for this check. "
            "Must be one of: 'Validation', 'State Conflict', 'Passive Awareness', 'Progression', 'Lore', or 'Resource'."
        )
    )
    
    session_id: str = Field(
        ..., 
        description="The unique session ID to track game state."
    )
class DndTools:
    """
    Factory for D&D game tools that interact with the Temporal Knowledge Graph (TKG) and Rules Engine.
    """
    def __init__(self, tkg, rules_agent=None):
        self.tkg = tkg
        self.rules_agent = rules_agent

    def get_buy_tool(self):
        @tool
        def buy_item(item_id: str, session_id: str) -> Dict[str, Any]:
            """
            Attempt to buy an item from a merchant. 
            Use this tool when the player explicitly states they want to purchase or buy a specific item.
            """
            # Implementation delegates to the TKG
            result = self.tkg.purchase_item(session_id, item_id)
            return {"result": result, "action": "buy_item", "item_id": item_id}
        return buy_item

    def get_sell_tool(self):
        @tool
        def sell_item(item_id: str, session_id: str) -> Dict[str, Any]:
            """
            Attempt to sell an item owned by the player.
            Use this tool when the player explicitly states they want to sell or lists an item to sell.
            """
            result = self.tkg.sell_item(session_id, item_id)
            return {"result": result, "action": "sell_item", "item_id": item_id}
        return sell_item

    def get_attack_tool(self):
        @tool
        def attack(target_id: str, session_id: str) -> Dict[str, Any]:
            """
            Attempt to attack a target in combat.
            Use this tool when the player explicitly wants to fight, attack, or strike a target.
            """
            result = self.tkg.attack(session_id, target_id)
            return {"result": result, "action": "attack", "target_id": target_id}
        return attack

    def get_create_character_tool(self):
        @tool
        def create_character(name: str, race: str, char_class: str, session_id: str) -> Dict[str, Any]:
            """
            Sets the player's Name, Race, and Class.
            Use this tool ONLY during character creation when the player provides these details.
            """
            result = self.tkg.update_player_profile(session_id, name, race, char_class)
            return {"result": result, "action": "create_character"}
        return create_character

    def get_check_rules_tool(self):
        @tool
        def check_rules(
            session_id: str,
            query: str,
            reason: str = "",
            player_input: str = "",
            previous_narrative_text: str = "",
            memory_context: str = "",
        ) -> Dict[str, Any]:
            """
            Proactively check whether D&D 5e mechanics should apply BEFORE narrating the next response.
            Call this tool once at the start of every turn.
            """
            print(f"⚖️ [Rules Lawyer] Checking: {query} (Reason: {reason})")
            if not self.rules_agent:
                return {
                    "action": "check_rules",
                    "error": "rules_agent_not_configured",
                    "should_check": False,
                    "query": query or "",
                    "reason": reason or "Rules agent unavailable.",
                    "rule_result": None,
                }

            if not query or not query.strip():
                return {
                    "action": "check_rules",
                    "error": "missing_query",
                    "should_check": False,
                    "query": "",
                    "reason": "No query provided. The narrator must pass a concrete rules question.",
                    "rule_result": None,
                }

            # Build current RPG state from TKG (avoid relying on the model to pass it correctly).
            stats = self.tkg.get_player_stats(session_id)
            inventory = self.tkg.get_inventory(session_id)
            rpg_context = (
                f"\n[RPG STATE]\n"
                f"Health: {stats.get('hp_current')}/{stats.get('hp_max')}\n"
                f"Gold: {stats.get('gold')}\n"
                f"Inventory: {[i['name'] for i in inventory]}\n"
                f"Session ID: {session_id}"
            )

            context: Dict[str, Any] = {
                "rpg_state": rpg_context,
                "memory_context": memory_context,
                "player_input": player_input,
                "narrative_text": previous_narrative_text,
                "session_id": session_id,
            }
            rule_result = self.rules_agent.adjudicate(query, context)
            return {
                "action": "check_rules",
                "should_check": True,
                "query": query,
                "reason": reason,
                "rule_result": (rule_result.explanation if rule_result else None),
            }

        return check_rules
