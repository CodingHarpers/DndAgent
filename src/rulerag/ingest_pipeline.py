from prompts import SYSTEM_PROMPT_ENTITY_LOGIC, SYSTEM_PROMPT_RULES, SYSTEM_PROMPT_CLASS
from google import genai
from google.genai.types import HttpOptions, Part
import dotenv
import json
from pathlib import Path
dotenv.load_dotenv()
from pydantic import BaseModel, Field
from typing import List, Optional
from google.genai import types
# --- A. For Spells, Features, Conditions, Items ---

class Mechanic(BaseModel):
    type: str = Field(..., description="Type of mechanic: 'constraint', 'effect', 'grant', or 'scaling'")
    trigger: str = Field(..., description="When does this apply? e.g. 'On Cast', 'Save Failed'")
    condition: str = Field(..., description="Logical requirement e.g. 'Target within 60ft'")
    outcome: str = Field(..., description="The mechanical result e.g. 'Deal 8d6 damage'")
    related_search_terms: List[str] = Field(..., description="Synonyms, slang, or related scenarios where this rule applies. E.g., for 'Sneak Attack', include ['backstab', 'surprise attack', 'rogue damage'].")

class EntityLogic(BaseModel):
    entity_name: str
    logic_type: str = Field(default="action_mechanic")
    mechanics: List[Mechanic]
    description_text: str = Field(
        ..., 
        description="The natural language text containing description, effects, and component requirements."
    )
    tags: List[str] = Field(default_factory=list)
    related_search_terms: List[str] = Field(default_factory=list)

class ClassLogic(BaseModel):
    class_name: str
    logic_type: str = Field(default="class_progression")
    mechanics: List[Mechanic]
    description_text: str = Field(
        ..., 
        description="The natural language text containing description, effects, and component requirements. Include Spellcasting Table here if available."
    )
    related_search_terms: List[str] = Field(default_factory=list)
# --- B. For Rule-Sections (Plain Text Rulebook) ---
class RuleLogic(BaseModel):
    premise: str = Field(..., description="The situation where this rule activates (IF...)")
    implication: str = Field(..., description="The mechanical change (THEN...)")
    exceptions: List[str] = Field(default_factory=list)
    description_text: str = Field(
        ..., 
        description="The summarized text from the rulebook. Critical for semantic retrieval and citation."
    )
    is_exception: bool = Field(default=False, description="True if this rule specifically overrides a general rule (Specific Beats General).")
    related_search_terms: List[str] = Field(default_factory=list)

class ExtractedConcept(BaseModel):
    concept_name: str
    definition: str
    rule_logic: RuleLogic
    related_keywords: List[str]

class RuleBookChunk(BaseModel):
    source_chapter: str
    extracted_concepts: List[ExtractedConcept]

class IngestPipeline:
    """
    Pipeline for ingesting raw text rules and converting them into structured JSON
    for the RuleRAG system.
    """
    def send_prompt(self, prompt: str, system_instruction=None, target_schema=None):
        client = genai.Client(http_options=HttpOptions(api_version="v1"))
        if system_instruction is None or target_schema is None:
            response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                )
            )
            return response.text
        else:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=target_schema
                )
            )
            return response.text
    def ingest_rule_text(self, text: str):
        # Placeholder for parsing logic
        pass
    def extract_data_to_kb(self, text: str, category: str):
        """
        Automatically select Prompt and Schema based on category
        """
        
        # Strategy routing: decide which logic to use
        if category in ["spells", "features", "conditions"]:
            # === Strategy A: Entity Extraction ===
            target_schema = EntityLogic
            system_instruction = SYSTEM_PROMPT_ENTITY_LOGIC
        
        elif category in ["rule-sections"]:
            # === Strategy B: Rule Extraction (Rule Book) ===
            target_schema = RuleBookChunk
            system_instruction = SYSTEM_PROMPT_RULES
        elif category in ["classes"]:
            target_schema = ClassLogic
            system_instruction = SYSTEM_PROMPT_CLASS
        else:
            raise ValueError(f"Unknown category: {category}")

        # Call Gemini (with structured output)
        try:
            response = self.send_prompt(text, system_instruction, target_schema)
            
            # Gemini will directly return JSON text that conforms to the Schema
            return json.loads(response)
            
        except Exception as e:
            print(f"Extraction failed: {e}")
            return None
if __name__ == "__main__":
    ingest_pipeline = IngestPipeline()
    fireball_text = """
    A bright streak flashes from your pointing finger to a point you choose within range...
    Each creature in a 20-foot-radius sphere centered on that point must make a Dexterity saving throw. 
    A target takes 8d6 fire damage on a failed save, or half as much damage on a successful one.
    """
    fireball_kb = ingest_pipeline.extract_data_to_kb(fireball_text, "spells")
    print(fireball_kb)