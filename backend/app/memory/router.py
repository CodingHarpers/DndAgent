from typing import Dict, Any
from app.memory.episodic_store import EpisodicStore
from app.memory.semantic_tkg import SemanticTKG

class MemoryRouter:
    def __init__(self, vector_store=None, graph_store=None):
        self.episodic = EpisodicStore()
        self.semantic = SemanticTKG()
        
    def retrieve_context(self, query: str, session_id: str) -> Dict[str, Any]:
        # 1. Episodic
        episodic_memories = self.episodic.search_memories(query, filters={"session_id": session_id})
        
        # 2. Semantic (simplified keyword extraction or entity linking)
        # Using a dummy ID for now
        semantic_facts = self.semantic.get_related_facts("dummy_location_id")
        
        return {
            "episodic": [m.dict() for m in episodic_memories],
            "semantic": semantic_facts
        }
