import os
import json
from typing import List, Any, Dict, Optional, Union
from dotenv import load_dotenv

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda

# New Google Gen AI SDK
from google import genai
from google.genai import types
from google.genai.types import HttpOptions

load_dotenv()

class GeminiAgent(Runnable):
    """
    Custom LangChain Runnable wrapper for the new Google Gen AI SDK (google-genai).
    """
    def __init__(self, model_name: str = "gemini-2.5-flash", tools: List[BaseTool] = None):
        self.model_name = model_name
        self.tools = tools or []
        
        # Initialize Client
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(
            api_key=api_key,
            http_options=HttpOptions(api_version="v1")
        )
        
        # Prepare tool config if tools exist
        self.gemini_tools = None
        if self.tools:
            self.gemini_tools = [self._convert_tool(t) for t in self.tools]

    def _convert_tool(self, tool: BaseTool) -> types.Tool:
        """
        Converts a LangChain tool to a Gemini Tool.
        """
        schema = tool.args_schema.schema() if tool.args_schema else {"properties": {}}
        return types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=schema
                )
            ]
        )

    def invoke(self, input: Dict[str, Any], config: Optional[RunnableConfig] = None) -> BaseMessage:
        messages = input["messages"]
        
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
            elif m.type == "tool": 
                parts = [types.Part(
                    function_response=types.FunctionResponse(
                        name=m.name,
                        response={"result": m.content} 
                    )
                )]
                contents.append(types.Content(
                    role="user",
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
                    tool_calls.append({
                        "name": part.function_call.name,
                        "args": part.function_call.args,
                        "id": f"call_{len(tool_calls)}",
                        "type": "tool_call"
                    })

        return AIMessage(content=content_text, tool_calls=tool_calls)

    def bind_tools(self, tools):
        self.tools = tools
        self.gemini_tools = [self._convert_tool(t) for t in tools]
        return self

class AgentFactory:
    """
    Factory to create configured generic agents (runnables).
    """
    @staticmethod
    def create_narrator(tools: List, model_name: str = "gemini-2.5-flash") -> Runnable:
        """
        Creates the Dungeon Master narrator agent using Google Gemini.
        """
        agent = GeminiAgent(model_name=model_name, tools=tools)

        # We keep the prompt template minimal now as the System Prompt is dynamically injected
        prompt = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="messages"),
        ])

        def agent_chain(input_dict):
            # 1. Run prompt
            prompt_val = prompt.invoke(input_dict)
            messages = prompt_val.to_messages()
            # 2. Run Agent
            return agent.invoke({"messages": messages})

        return RunnableLambda(agent_chain)
