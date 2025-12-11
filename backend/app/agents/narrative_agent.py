import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# LangChain core
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import BaseTool

# Google Gen AI SDK
from google import genai
from google.genai import types
from google.genai.types import HttpOptions

load_dotenv()

class NarrativeAgent(Runnable):
    """
    Narrative Agent using Google Gemini (via google-genai SDK).
    
    This agent acts as the primary interface to the LLM. It:
    1. Accepts a list of messages (conversation history).
    2. Has tools bound to it (Buy, Sell, Attack).
    3. Returns an AIMessage which may contain text OR tool calls.
    
    It mimics the behavior of a LangChain ChatModel but uses the new SDK directly
    for better control and latest features.
    """
    
    def __init__(self, model_name: str = "gemini-2.5-flash", tools: List = None):
        self.model_name = model_name
        self.tools = tools or []
        
        # Initialize Client
        # Ensure GEMINI_API_KEY is in .env
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(
            api_key=api_key,
            http_options=HttpOptions(api_version="v1beta")
        )
        
        # Prepare tool config if tools exist
        self.gemini_tools = None
        if self.tools:
            self.gemini_tools = [self._convert_tool(t) for t in self.tools]

    def _convert_tool(self, tool: Any) -> types.Tool:
        """
        Converts a LangChain tool (or compatible object) to a Gemini Tool.
        """
        # If it's a LangChain tool, it has args_schema.
        if hasattr(tool, "args_schema") and tool.args_schema:
            schema = tool.args_schema.schema()
        # If it's a simple function decorated with @tool, we might need to inspect it differently
        # But standard @tool usage creates a StructuredTool with args_schema.
        else:
            schema = {"properties": {}} # Fallback

        return types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=schema
                )
            ]
        )

    def bind_tools(self, tools: List):
        """
        Binds a list of tools to this agent, enabling the LLM to call them.
        """
        self.tools = tools
        self.gemini_tools = [self._convert_tool(t) for t in tools]
        return self

    def invoke(self, input: List[BaseMessage] | Dict[str, Any], config: Optional[RunnableConfig] = None) -> BaseMessage:
        """
        Invokes the model with the given messages.
        Input can be a list of messages or a dict with "messages" key.
        """
        if isinstance(input, dict):
            messages = input["messages"]
        else:
            messages = input
        
        # 1. Convert Messages to Gemini Content
        contents = []
        system_instruction_parts = []

        for m in messages:
            if isinstance(m, SystemMessage):
                if m.content:
                    system_instruction_parts.append(m.content)
            elif isinstance(m, HumanMessage):
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part(text=m.content)]
                ))
            elif isinstance(m, AIMessage):
                parts = []
                if m.content:
                    parts.append(types.Part(text=m.content))
                if m.tool_calls:
                    for tc in m.tool_calls:
                        parts.append(types.Part(
                            function_call=types.FunctionCall(
                                name=tc["name"],
                                args=tc["args"]
                            )
                        ))
                
                contents.append(types.Content(
                    role="model",
                    parts=parts
                ))
            # Handle Tool Messages (Results of tool execution)
            elif m.type == "tool": 
                # LangGraph ToolMessage: content is result, name is tool name, tool_call_id is id
                parts = [types.Part(
                    function_response=types.FunctionResponse(
                        name=m.name,
                        response={"result": m.content} 
                    )
                )]
                contents.append(types.Content(
                    role="user", # Tool outputs are 'user' role in Gemini
                    parts=parts
                ))
        
        system_instruction = "\n\n".join(system_instruction_parts) if system_instruction_parts else None

        # 2. Configure Tools
        tool_config = None
        if self.gemini_tools:
            tool_config = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="AUTO"
                )
            )

        # 3. Call API
        generate_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=self.gemini_tools,
            tool_config=tool_config,
            temperature=0.7
        )

        try:
            print(f"[NarrativeAgent] Generating with {len(messages)} messages...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=generate_config
            )

            # 4. Convert Response to AIMessage
            content_text = ""
            tool_calls = []

            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        content_text += part.text
                    if part.function_call:
                        # Convert arguments to dict
                        args_dict = {}
                        if part.function_call.args:
                            try:
                                args_dict = dict(part.function_call.args)
                            except:
                                args_dict = part.function_call.args
                        
                        tool_calls.append({
                            "name": part.function_call.name,
                            "args": args_dict,
                            "id": f"call_{len(tool_calls)}_{os.urandom(4).hex()}",
                            "type": "tool_call"
                        })
            
            print(f"[NarrativeAgent] Generation successful. Tool Calls: {len(tool_calls)}")
            return AIMessage(content=content_text, tool_calls=tool_calls)

        except Exception as e:
            print(f"[NarrativeAgent] Error: {e}")
            return AIMessage(content=f"I encountered an error processing your request: {e}")
