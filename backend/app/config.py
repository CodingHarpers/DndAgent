import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App
    APP_NAME: str = "ARCANA"
    DEBUG: bool = True
    
    # LLM
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    LLM_MODEL_NAME: str = "gemini-1.5-flash"
    EMBEDDING_MODEL_NAME: str = "models/embedding-001"

    # Databases
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")

    VECTOR_STORE_PATH: str = "chroma_db"
    
    # Paths
    RULES_KB_PATH: str = "app/data/rules_kb.json"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
