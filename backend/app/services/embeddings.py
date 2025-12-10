from openai import OpenAI
from typing import List, Union
from app.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def embed(texts: Union[str, List[str]]) -> List[List[float]]:
    """
    Generate embeddings for text(s) using OpenAI.
    Returns a list of vectors.
    """
    if isinstance(texts, str):
        texts = [texts]
        
    if not texts:
        return []

    # Ensure clean inputs
    texts = [t.replace("\n", " ") for t in texts]

    return [
        d.embedding
        for d in client.embeddings.create(
            model=settings.EMBEDDING_MODEL_NAME, # Should be "text-embedding-3-small"
            input=texts
        ).data
    ]

def get_single_embedding(text: str) -> List[float]:
    """Helper for single string embedding"""
    vectors = embed(text)
    if not vectors:
        return [0.0] * 1536 # Default dimensionality for text-embedding-3-small
    return vectors[0]
