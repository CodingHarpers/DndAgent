from google.genai import types

# Define schemas for parameters using types.Schema
buy_item_params = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "item_id": types.Schema(
            type=types.Type.STRING,
            description="The ID of the item to buy (e.g., 'item_rusty_sword')."
        )
    },
    required=["item_id"]
)

sell_item_params = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "item_id": types.Schema(
            type=types.Type.STRING,
            description="The ID of the item to sell."
        )
    },
    required=["item_id"]
)

# Define FunctionDeclarations
buy_item_func = types.FunctionDeclaration(
    name="buy_item",
    description="Attempt to buy an item from a merchant. Use this when the player explicitly wants to purchase something.",
    parameters=buy_item_params
)

sell_item_func = types.FunctionDeclaration(
    name="sell_item",
    description="Attempt to sell an item owned by the player. Use this when the player explicitly wants to sell something.",
    parameters=sell_item_params
)

# Create the Tool object
dnd_tool_instance = types.Tool(function_declarations=[buy_item_func, sell_item_func])

# Export as a list, because GenerateContentConfig.tools expects a list of Tool objects
dnd_tools = [dnd_tool_instance]
