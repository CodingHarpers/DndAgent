<<<<<<< HEAD:src/storytelling/tools.py
from typing import Dict, Any, Optional
from langchain_core.tools import tool

# We will define tools that can be bound to our agents.
# These need to be initialized with access to the actual subsystems (Memory, Rules).
# Since tools are often static functions or need specific setup, we can use a factory or closure pattern, 
# or just simple functions if we pass context.

# However, standard @tool decorators work best with global or injected state.
# For simplicity, we'll define a class to hold the tools which gets initialized with the subsystems.

class StorytellingTools:
    def __init__(self, memory_router, rules_lawyer):
        self.memory = memory_router
        self.rules = rules_lawyer

    def retrieve_memory_tool(self):
        @tool
        def retrieve_context(query: str) -> Dict[str, Any]:
            """Retrieve relevant context (episodic and semantic) from memory based on the query."""
            return self.memory.retrieve_context(query)
        return retrieve_context

    def adjudicate_rule_tool(self):
        @tool
        def check_rule(action_desc: str, die_roll: int) -> Dict[str, Any]:
            """Check the rules for a specific action description using a provided die roll result. Returns outcome."""
            # In a real app, we'd probably parse the action to find the right rule
            # For now, we mock the rule_json
            return self.rules.adjudicate(
                action_intent=action_desc,
                rule_json={"difficulty_class": 12, "success_outcome": "Action succeeds"},
                die_roll=die_roll
            )
        return check_rule

    def dice_roll_tool(self):
        @tool
        def roll_die(sides: int = 20) -> Dict[str, Any]:
            """Roll a die (default d20) to determine the success of an action or event."""
            result = self.rules.roll_die(sides)
            return {"result": result, "sides": sides}
        return roll_die
=======
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool

buy_item_func = FunctionDeclaration(
    name="buy_item",
    description="Attempt to buy an item from a merchant. Use this when the player explicitly wants to purchase something.",
    parameters={
        "type": "OBJECT",
        "properties": {
            "item_id": {
                "type": "STRING",
                "description": "The ID of the item to buy (e.g., 'item_rusty_sword')."
            }
        },
        "required": ["item_id"]
    }
)

sell_item_func = FunctionDeclaration(
    name="sell_item",
    description="Attempt to sell an item owned by the player. Use this when the player explicitly wants to sell something.",
    parameters={
        "type": "OBJECT",
        "properties": {
            "item_id": {
                "type": "STRING",
                "description": "The ID of the item to sell."
            }
        },
        "required": ["item_id"]
    }
)

# The SDK expects a Tool object wrapping the declarations
dnd_tools = Tool(function_declarations=[buy_item_func, sell_item_func])
>>>>>>> main:backend/app/agents/tools.py
