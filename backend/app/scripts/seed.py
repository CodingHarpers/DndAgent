from app.memory.semantic_tkg import SemanticTKG
from app.models.schemas import EntityNode, RelationshipEdge
import time

def seed_world():
    print("🌱 Starting World Seed...")
    tkg = SemanticTKG()
    
    # Optional: Clear DB first? 
    # For now, we'll just MERGE so it's idempotent-ish
    
    # --- Locations ---
    locations = [
        EntityNode(id="loc_greenhollow", label="Location", properties={"name": "Greenhollow Village", "description": "A peaceful village on the edge of the Eldwood.", "type": "Village"}),
        EntityNode(id="loc_rusty_tankard", label="Location", properties={"name": "The Rusty Tankard", "description": "A warm and lively inn, smelling of roast pork and ale.", "type": "Inn"}),
        EntityNode(id="loc_blacksmith", label="Location", properties={"name": "Brim's Anvil", "description": "The loud and hot workshop of the village smith.", "type": "Shop"}),
        EntityNode(id="loc_eldwood", label="Location", properties={"name": "Eldwood Forest", "description": "A dense, ancient forest said to hold forgotten secrets.", "type": "Forest"}),
        EntityNode(id="loc_crypt", label="Location", properties={"name": "Ancient Crypt", "description": "A stone door embedded in a hillside, sealed for centuries.", "type": "Dungeon"}),
        # User Data
        EntityNode(id="loc_eldermere", label="Location", properties={"name": "Eldermere", "type": "City"}),
    ]
    
    # --- Factions (New) ---
    factions = [
        EntityNode(id="fac_royal_council", label="Faction", properties={"name": "Royal Council"}),
    ]

    # --- NPCs ---
    npcs = [
        EntityNode(id="npc_elara", label="Character", properties={"name": "Elara", "role": "Innkeeper", "personality": "Cheerful, gossip-loving"}),
        EntityNode(id="npc_brim", label="Character", properties={"name": "Brim", "role": "Blacksmith", "personality": "Gruff but kind-hearted"}),
        EntityNode(id="npc_thorne", label="Character", properties={"name": "Elder Thorne", "role": "Village Elder", "personality": "Wise, worried about the forest"}),
        EntityNode(id="npc_gark", label="Character", properties={"name": "Gark", "role": "Goblin Scout", "personality": "Skittish, greedy"}),
        # User Data
        EntityNode(id="npc_king_aldric", label="Character", properties={"name": "King Aldric", "role": "King"}),
    ]

    # --- Items ---
    items = [
        EntityNode(id="item_rusty_sword", label="Item", properties={"name": "Rusty Sword", "damage": "1d6", "value": "5gp"}),
        EntityNode(id="item_map", label="Item", properties={"name": "Old Map", "description": "A map showing a hidden path in the Eldwood."}),
    ]
    
    print(f"Adding {len(locations)} locations...")
    for loc in locations:
        tkg.add_entity(loc)

    print(f"Adding {len(npcs)} NPCs...")
    for npc in npcs:
        tkg.add_entity(npc)

    print(f"Adding {len(items)} Items...")
    for item in items:
        tkg.add_entity(item)
    
    print(f"Adding {len(factions)} Factions...")
    for fac in factions:
        tkg.add_entity(fac)

    # --- Relationships ---
    relationships = [
        # Locations
        RelationshipEdge(source_id="loc_greenhollow", target_id="loc_rusty_tankard", type="CONTAINS"),
        RelationshipEdge(source_id="loc_greenhollow", target_id="loc_blacksmith", type="CONTAINS"),
        RelationshipEdge(source_id="loc_greenhollow", target_id="loc_eldwood", type="ADJACENT_TO"),
        RelationshipEdge(source_id="loc_eldwood", target_id="loc_crypt", type="CONTAINS", properties={"hidden": True}),
        
        # NPCs
        RelationshipEdge(source_id="npc_elara", target_id="loc_rusty_tankard", type="WORKS_AT"),
        RelationshipEdge(source_id="npc_brim", target_id="loc_blacksmith", type="OWNS"),
        RelationshipEdge(source_id="npc_thorne", target_id="loc_greenhollow", type="LEADS"),
        RelationshipEdge(source_id="npc_gark", target_id="loc_eldwood", type="LIVES_IN"),
        
        # Social
        RelationshipEdge(source_id="npc_brim", target_id="npc_elara", type="FRIEND_OF"),
        
        # Items
        RelationshipEdge(source_id="npc_thorne", target_id="item_map", type="HAS_POSSESSION"),

        # User Data
        RelationshipEdge(source_id="npc_king_aldric", target_id="loc_eldermere", type="RULES", properties={"since": "today"}),
        RelationshipEdge(source_id="npc_king_aldric", target_id="fac_royal_council", type="LEADS"),
    ]

    print(f"Adding {len(relationships)} relationships...")
    for rel in relationships:
        tkg.add_relationship(rel)

    tkg.close()
    print("✅ World Seed Complete!")

if __name__ == "__main__":
    seed_world()
