from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

# --- Shared / Core Models ---

class AgentMessage(BaseModel):
    source: str
    target: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# --- Memory Models ---

class MemoryRecord(BaseModel):
    session_id: str
    timestamp: datetime
    speaker: str
    event_type: str  # e.g., "dialogue", "action", "system"
    summary: str
    raw_text: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EntityProperties(BaseModel):
    """
    Common properties for entities to ensure schema compatibility with Gemini API.
    """
    model_config = ConfigDict(extra='allow')
    
    name: Optional[str] = None
    description: Optional[str] = None
    value: Optional[str] = None # For items
    role: Optional[str] = None # For characters
    type: Optional[str] = None # For locations/items
    status: Optional[str] = None
    # Flexible catch-all for other simple fields if strictly needed, but kept minimal for schema
    
class RelationshipProperties(BaseModel):
    """
    Properties for relationships.
    """
    model_config = ConfigDict(extra='allow')

    context: Optional[str] = None # Why this rel exists?
    weight: Optional[int] = 1

class EntityNode(BaseModel):
    id: str  # Unique ID in TKG
    label: str  # e.g., "Character", "Location"
    properties: EntityProperties

class RelationshipEdge(BaseModel):
    source_id: str
    target_id: str
    type: str  # e.g., "LOCATED_IN", "KNOWS"
    properties: RelationshipProperties = Field(default_factory=RelationshipProperties)

# --- Rule Models ---

class RuleEntry(BaseModel):
    rule_id: str
    title: str
    section: str
    tags: List[str]
    content: str
    prerequisites: Optional[str] = None
    effects: Optional[str] = None
    exceptions: Optional[str] = None
    source_ref: str

class RuleAdjudicationRequest(BaseModel):
    query: str
    context: str

class RuleAdjudicationResult(BaseModel):
    explanation: str

# --- Narrative / Scene Models ---

class Scene(BaseModel):
    scene_id: str
    title: str
    narrative_text: str
    location: str
    characters_present: List[str]
    world_state_diff: Dict[str, Any] = Field(default_factory=dict)
    available_actions: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)

# --- API Request/Response Models ---

class SessionStartRequest(BaseModel):
    player_name: str
    campaign_setting: Optional[str] = "Standard Fantasy"

class PlayerInput(BaseModel):
    session_id: str
    text: str

class WorldExtractionResult(BaseModel):
    entities: List[EntityNode] = Field(default_factory=list)
    relationships: List[RelationshipEdge] = Field(default_factory=list)

# --- RPG Mechanics Models ---

class PlayerStats(BaseModel):
    name: Optional[str] = "Traveler"
    race: Optional[str] = None
    char_class: Optional[str] = Field(None, alias="class")
    hp_current: int
    hp_max: int
    gold: int
    power: int
    speed: int

    model_config = ConfigDict(populate_by_name=True)

class InventoryItem(BaseModel):
    id: str
    name: str
    type: str # e.g. "Weapon", "Potion"
    properties: Dict[str, Any] = Field(default_factory=dict)

class BuyRequest(BaseModel):
    session_id: str # used to identify player
    item_id: str

# Update TurnResponse to include stats
class TurnResponse(BaseModel):
    scene: Scene
    rule_outcome: Optional[RuleAdjudicationResult] = None
    player_stats: Optional[PlayerStats] = None
    action_log: Optional[Dict[str, Any]] = None


