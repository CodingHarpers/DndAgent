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
