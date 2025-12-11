from typing import List, Dict, Any, Type, Optional
from google import genai
from google.genai import types
from google.genai.types import HttpOptions
from app.config import settings
import json
import traceback
import dotenv
import os

dotenv.load_dotenv()

class GenerationClient:
    def __init__(self):
        # Configure the client as requested (relying on env vars or default creds)
        self.client = genai.Client(
            http_options=HttpOptions(api_version="v1")
        )
        self.model_name = settings.LLM_MODEL_NAME

    def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
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
            # Use native structured output if available
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=response_model,
                    temperature=0.2 
                )
            )
            
            text = response.text
            if not text:
                return None
            
            # Clean up potential markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
                
            return response_model.model_validate_json(text.strip())
        except Exception as e:
            print(f"LLM Native Structured Error: {e}")
            print("Falling back to standard generation...")
            
            # Fallback: Retry with manual schema injection
            try:
                schema_json = json.dumps(response_model.model_json_schema())
                fallback_instruction = (
                    f"{system_prompt}\n\n"
                    f"You MUST output a valid JSON OBJECT INSTANCE that matches the following schema. "
                    f"Do NOT output the schema definition itself.\n\n"
                    f"Schema:\n{schema_json}"
                )
                
                # For fallback, we just append user prompt to system instruction as a simple content
                fallback_prompt = f"{fallback_instruction}\n\nUser Input: {user_prompt}"
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=fallback_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                text = response.text
                if not text:
                    return None
                
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]
                return response_model.model_validate_json(text.strip())
            except Exception as e2:
                print(f"LLM Fallback Error: {e2}")
                return None

    
    def generate_with_tools(self, system_prompt: str, user_prompt: str, tools: List[Any]) -> Any:
        """
        Generates content using tool calling capabilities.
        Returns the raw response to allow inspection of function calls.
        """
        try:
            # The google.genai SDK supports passing a list of Tool objects
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=tools, # Pass tools here
                    temperature=0.1 # Low temp for tool precision
                )
            )
            return response
            
        except Exception as e:
            traceback.print_exc()
            print(f"LLM Tool Gen Error: {repr(e)}")
            return None

# Singleton instance
generation_client = GenerationClient()
