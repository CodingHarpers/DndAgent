from typing import Dict, Any, Optional
from langchain_core.tools import tool

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
