import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any
from app.models.schemas import MemoryRecord
from app.services.llm_client import llm_client
from app.config import settings
import uuid

class EpisodicStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.VECTOR_STORE_PATH)
        self.collection = self.client.get_or_create_collection("episodic_memory")

    def add_memory(self, record: MemoryRecord):
        if not record.embedding:
            record.embedding = llm_client.get_embedding(record.raw_text)
        
        self.collection.add(
            documents=[record.raw_text],
            metadatas=[{
                "session_id": record.session_id,
                "timestamp": record.timestamp.isoformat(),
                "speaker": record.speaker,
                "event_type": record.event_type,
                "summary": record.summary,
                **record.metadata
            }],
            ids=[str(uuid.uuid4())],
            embeddings=[record.embedding]
        )

    def search_memories(self, query: str, limit: int = 5, filters: Dict = None) -> List[MemoryRecord]:
        embedding = llm_client.get_embedding(query)
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=limit,
            where=filters
        )
        
        memories = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                memories.append(MemoryRecord(
                    session_id=meta.get("session_id", "unknown"),
                    timestamp=meta.get("timestamp"), # Needs parsing back to datetime if strict
                    speaker=meta.get("speaker", ""),
                    event_type=meta.get("event_type", ""),
                    summary=meta.get("summary", ""),
                    raw_text=doc,
                    metadata=meta
                ))
        return memories
