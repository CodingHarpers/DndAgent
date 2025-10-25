import os
import json
from typing import List, Any, Dict, Optional, Union
from dotenv import load_dotenv

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import BaseTool

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
        # The SDK automatically picks up GOOGLE_API_KEY or GEMINI_API_KEY from env if not passed.
        # But user provided specific keys and Vertex flag.
        api_key = os.getenv("GEMINI_API_KEY")
        # Check if we should use Vertex AI (though the user snippet implies direct client init with version)
        # The user's snippet: client = genai.Client(http_options=HttpOptions(api_version="v1"))
        # We will follow that.
        
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
        # This is a simplification. Real conversion needs to map JSON schema types.
        # For this prototype, we'll try to use the function declarations.
        
        # We need to construct a FunctionDeclaration
        # types.FunctionDeclaration(...)
        
        # For simplicity, we might need to rely on the SDK's automatic conversion if available,
        # or manually map the schema.
        # Let's inspect what tool.args_schema.schema() gives us.
        
        schema = tool.args_schema.schema() if tool.args_schema else {"properties": {}}
        
        # Helper to map JSON schema types to Gemini types
        # Note: This part can be tricky.
        
        # Let's try to construct a minimal declaration.
        return types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=schema # The SDK often accepts the JSON schema dict directly for parameters
                )
            ]
        )

    def invoke(self, input: Dict[str, Any], config: Optional[RunnableConfig] = None) -> BaseMessage:
        messages = input["messages"]
        
        # 1. Convert Messages to Gemini Content
        contents = []
        system_instruction = None

        for m in messages:
            if isinstance(m, SystemMessage):
                system_instruction = m.content
            elif isinstance(m, HumanMessage):
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part(text=m.content)]
                ))
            elif isinstance(m, AIMessage):
                parts = []
                if m.content:
                    parts.append(types.Part(text=m.content))
                # If there are tool calls, we need to represent them.
                # In LangChain, tool_calls are in m.tool_calls.
                # In Gemini, they are FunctionCall parts.
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
            # Handle ToolMessage (results of tool execution)
            elif m.type == "tool": 
                # LangChain ToolMessage has tool_call_id and content
                # Gemini expects a FunctionResponse
                # We need to match the tool_call_id to the function call, but Gemini v1 API 
                # mainly cares about the function name in the response usually.
                # However, v1beta/v1 often tracks order.
                
                # We need to find the name of the tool from the previous AIMessage or context.
                # LangChain doesn't store the name in ToolMessage by default in all versions.
                # But ToolNode usually returns name.
                
                parts = [types.Part(
                    function_response=types.FunctionResponse(
                        name=m.name, # Ensure our ToolNode populates this or we infer it
                        response={"result": m.content} 
                    )
                )]
                contents.append(types.Content(
                    role="user", # Function responses are sent as 'user' or 'function' role depending on API version
                    parts=parts
                ))

        # 2. Configure Tools
        tool_config = None
        if self.gemini_tools:
            tool_config = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="AUTO"
                )
            )

        # 3. Call API
        # The user used 'client.models.generate_content'
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
        # We need to parse parts for text and function calls
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
                        "id": f"call_{len(tool_calls)}", # Dummy ID as Gemini doesn't always return one
                        "type": "tool_call"
                    })

        return AIMessage(content=content_text, tool_calls=tool_calls)

    def bind_tools(self, tools):
        # LangChain calls this to bind tools. 
        # Since we initialized with tools or can set them, we update self.
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
        # Create our custom agent
        agent = GeminiAgent(model_name=model_name, tools=tools)

        # We construct the prompt logic inside the invoke or wrapped
        # But here we just return the agent which handles messages directly.
        
        # However, the Orchestrator passes a dictionary with 'messages'.
        # Our GeminiAgent.invoke handles that.
        
        # We might need to wrap it in a RunnableLambda if we wanted to use prompts separately,
        # but Gemini supports system_instruction in config, so we can pass that in the agent logic
        # or prepend it to messages.
        
        # The Orchestrator uses: agent = prompt | llm_with_tools
        # Where prompt is a ChatPromptTemplate.
        
        # If we return just 'agent', it will receive the output of 'prompt.invoke(...)', 
        # which is a formatting of messages.
        
        # So we can keep the prompt template in Orchestrator or here.
        # Let's recreate the chain.
        
        prompt = ChatPromptTemplate.from_messages([
            # We move system instruction to the agent handling or keep it as SystemMessage
            ("system", "You are the Dungeon Master (DM) for a D&D 5e game. "
                       "Your goal is to narrate the story, describe the environment, and respond to player actions. "
                       "You have access to tools to look up memory/context and check rules. "
                       "ALWAYS check rules for combat or risky actions. "
                       "ALWAYS check memory if the player references past events or NPCs you don't recall immediately."),
            MessagesPlaceholder(variable_name="messages"),
        ])

        # When prompt is invoked, it produces a ChatPromptValue.
        # We need our agent to accept ChatPromptValue or the dict/list of messages.
        # Runnable 'prompt' outputs StringPromptValue or ChatPromptValue.
        # ChatPromptValue.to_messages() returns the list of messages.
        
        def agent_chain(input_dict):
            # 1. Run prompt
            prompt_val = prompt.invoke(input_dict)
            messages = prompt_val.to_messages()
            
            # 2. Run Agent
            return agent.invoke({"messages": messages})

        return RunnableLambda(agent_chain)

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
