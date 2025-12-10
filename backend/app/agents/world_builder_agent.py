from typing import Dict, Any, List
from app.models.schemas import Scene, WorldExtractionResult
from app.services.generation import generation_client
from app.memory.semantic_tkg import SemanticTKG

class WorldBuilderAgent:
    def __init__(self):
        self.tkg = SemanticTKG()

    def update_world(self, scene: Scene):
        """
        Extracts new world facts (Entities and Relationships) from the scene
        and updates the Semantic TKG.
        """
        print("[WorldBuilderAgent] Extracting world updates...")
        
        system_prompt = (
            "You are a Knowledge Graph Engineer for a D&D game. "
            "Extract new or updated entities and relationships from the narrative. "
            "Entities MUST use one of these labels: 'Character', 'Location', 'Item', 'Faction', 'Quest'. "
            "Ignore transient events. "
            "IMPORTANT: Use snake_case for IDs (e.g., 'character_gark', 'loc_dungeon_entrance')."
        )
        
        user_prompt = f"Narrative:\n{scene.narrative_text}\n\nLocation: {scene.location}\nCharacters: {scene.characters_present}"
        
        try:
            updates: WorldExtractionResult = generation_client.generate_structured(
                system_prompt,
                user_prompt,
                WorldExtractionResult
            )
            
            # Persist to Neo4j
            count_entities = 0
            for entity in updates.entities:
                self.tkg.add_entity(entity)
                count_entities += 1
                
            count_rels = 0
            for rel in updates.relationships:
                self.tkg.add_relationship(rel)
                count_rels += 1
                
            print(f"[WorldBuilderAgent] Updated TKG: {count_entities} entities, {count_rels} relationships.")

        except Exception as e:
            print(f"[WorldBuilderAgent] Update failed: {e}")
