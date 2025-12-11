from typing import List, Dict, Any, Type, Optional
from pydantic import BaseModel
from google import genai
from google.genai import types
from app.config import settings
import json
import os

class GenerationClient:
    def __init__(self):
        # Configure the client with the new SDK
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(api_version="v1beta")
        )
        self.model_name = settings.LLM_MODEL_NAME

    def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        try:
            print(f"[GenerationClient] Text Gen: {user_prompt[:50]}...")
            # Construct content
            # New SDK prefers system instructions in config or separate
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(role="user", parts=[types.Part(text=user_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature
                )
            )
            return response.text or ""
        except Exception as e:
            print(f"LLM Text Error: {e}")
            return "Thinking... (Error in AI generation)"

    def generate_structured(self, system_prompt: str, user_prompt: str, response_model: Type[Any]) -> Any:
        try:
            # The new SDK supports response_schema and response_mime_type with Pydantic
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(role="user", parts=[types.Part(text=user_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.2, # Lower temperature for structural stability
                    response_mime_type="application/json",
                    response_schema=self._get_clean_schema(response_model)
                )
            )
            
            # The new SDK might return a parsed object if configured, but typically returns text/json
            # Use Pydantic to validate
            text = response.text
            # Basic cleanup just in case
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
                
            return response_model.model_validate_json(text.strip())
            
        except Exception as e:
            print(f"LLM Native Structured Error: {e}")
            return None # Or raise

    def generate_with_tools(self, system_prompt: str, user_prompt: str, tools: Any = None) -> Any:
        """
        Generates content using tool calling capabilities.
        Returns the raw GenerateOptionResponse.
        """
        try:
            # If 'tools' is passed, it should be a list of types.Tool or equivalent
            gemini_tools = None
            if tools:
                # If it's already a types.Tool (like from tools.py refactor), use it directly
                # If it's a list, wrap it? Use logic from agents.py if needed.
                # Assuming 'tools' passed here is compatible or needs conversion.
                # For backward compat with old 'dnd_tools' variable if it wasn't refactored:
                gemini_tools = [tools] if not isinstance(tools, list) else tools

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(role="user", parts=[types.Part(text=user_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=gemini_tools,
                    temperature=0.1
                )
            )
            return response
            
        except Exception as e:
            print(f"LLM Tool Gen Error: {repr(e)}")
            return None

    def _get_clean_schema(self, pydantic_model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generates a JSON schema from a Pydantic model and removes 'additionalProperties'
        fields which are not supported by the Gemini API.
        """
        schema = pydantic_model.model_json_schema()
        
        def clean_recursive(node):
            if isinstance(node, dict):
                if "additionalProperties" in node:
                    del node["additionalProperties"]
                # Also remove 'title' if present as it adds noise, though usually allowed
                # if "title" in node:
                #    del node["title"]
                for key, value in node.items():
                    clean_recursive(value)
            elif isinstance(node, list):
                for item in node:
                    clean_recursive(item)
                    
        clean_recursive(schema)
        return schema

# Singleton instance
generation_client = GenerationClient()
