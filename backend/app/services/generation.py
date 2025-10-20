from typing import List, Dict, Any, Type
import google.generativeai as genai
from app.config import settings
import json

class GenerationClient:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.LLM_MODEL_NAME)

    def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        try:
            # Gemini Pattern: "System Prompt" as first User message
            messages = [
                {"role": "user", "parts": [{"text": system_prompt}]},
                {"role": "user", "parts": [{"text": user_prompt}]}
            ]
            
            response = self.model.generate_content(
                messages,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature
                )
            )
            return response.text
        except Exception as e:
            print(f"LLM Text Error: {e}")
            return "Thinking... (Error in AI generation)"

    def generate_structured(self, system_prompt: str, user_prompt: str, response_model: Type[Any]) -> Any:
        # Create schema definition
        schema_json = json.dumps(response_model.model_json_schema())
        
        # Construct messages following the "System as User" pattern
        # Explicitly instruct JSON output in the prompt logic as well
        system_instruction = (
            f"{system_prompt}\n\n"
            f"You MUST output valid JSON only, matching this schema:\n{schema_json}"
        )
        
        messages = [
            {"role": "user", "parts": [{"text": system_instruction}]},
            {"role": "user", "parts": [{"text": user_prompt}]}
        ]

        try:
            response = self.model.generate_content(
                messages,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.2 # Lower temperature for structural stability
                )
            )
            
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
                
            return response_model.model_validate_json(text.strip())
        except Exception as e:
            print(f"LLM Native Structured Error: {e}")
            print("Falling back to standard generation...")
            
            # Fallback: Retry with simple text generation if structured mode fails
            # Sometimes models or old keys struggle with JSON mode
            try:
                fallback_messages = [
                    {"role": "user", "parts": [{"text": f"{system_instruction}\n\nUser Input: {user_prompt}"}]}
                ]
                response = self.model.generate_content(fallback_messages)
                text = response.text
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]
                return response_model.model_validate_json(text.strip())
            except Exception as e2:
                print(f"LLM Fallback Error: {e2}")
                return None

# Singleton instance
generation_client = GenerationClient()
