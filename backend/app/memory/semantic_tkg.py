from neo4j import GraphDatabase
from typing import List, Dict, Any
from app.models.schemas import EntityNode, RelationshipEdge
from app.config import settings

class SemanticTKG:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI, 
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def add_entity(self, entity: EntityNode):
        # Sanitize label by wrapping in backticks to handle spaces
        label = f"`{entity.label}`"
        query = (
            f"MERGE (n:{label} {{id: $id}}) "
            "SET n += $props"
        )
        with self.driver.session() as session:
            session.run(query, id=entity.id, props=entity.properties)

    def add_relationship(self, rel: RelationshipEdge):
        # Sanitize type by wrapping in backticks
        rel_type = f"`{rel.type}`"
        query = (
            "MATCH (a {id: $source_id}), (b {id: $target_id}) "
            f"MERGE (a)-[r:{rel_type}]->(b) "
            "SET r += $props"
        )
        with self.driver.session() as session:
            session.run(query, source_id=rel.source_id, target_id=rel.target_id, props=rel.properties)

    def query_subgraph(self, cypher_query: str, params: Dict = None) -> List[Dict]:
        with self.driver.session() as session:
            result = session.run(cypher_query, params or {})
            return [record.data() for record in result]

    def get_related_facts(self, entity_id: str) -> List[str]:
        query = """
        MATCH (n {id: $id})-[r]-(m)
        RETURN n.id, type(r), m.id, m
        LIMIT 10
        """
        facts = []
        with self.driver.session() as session:
            result = session.run(query, id=entity_id)
            for record in result:
                facts.append(f"{record['n.id']} {record['type(r)']} {record['m.id']}")
        return facts

    # --- RPG Mechanics ---

    # --- RPG Mechanics ---

    def create_player(self, session_id: str, name: str, stats: Dict[str, Any]):
        """Creates or merges a Player Character node. Uses a static ID for single-player persistence."""
        pid = "player_main" # Static ID for single player MVP
        
        query = (
            "MERGE (p:Character {id: $id}) "
            "ON CREATE SET "
            "    p.name = $name, "
            "    p.hp_current = $hp, "
            "    p.hp_max = $hp_max, "
            "    p.gold = $gold, "
            "    p.power = $power, "
            "    p.speed = $speed, "
            "    p.is_player = true "
            "ON MATCH SET "
            "    p.name = $name " 
        )
        # Note: We only set stats ON CREATE so we don't overwrite progress on re-session
        
        with self.driver.session() as session:
            session.run(query, id=pid, name=name, 
                        hp=stats['hp_current'], hp_max=stats['hp_max'], 
                        gold=stats['gold'], power=stats['power'], speed=stats['speed'])
            
    def get_player_stats(self, session_id: str) -> Dict[str, Any]:
        pid = "player_main"
        query = "MATCH (p:Character {id: $id}) RETURN p"
        with self.driver.session() as session:
            result = session.run(query, id=pid).single()
            if result:
                props = result['p']
                return {
                    "hp_current": props.get("hp_current", 10),
                    "hp_max": props.get("hp_max", 10),
                    "gold": props.get("gold", 0),
                    "power": props.get("power", 10),
                    "speed": props.get("speed", 10)
                }
            return {}

    def get_inventory(self, session_id: str) -> List[Dict]:
        pid = "player_main"
        # Use WHERE type(r) = 'OWNS' to avoid Neo4j warning if relationship type doesn't exist yet
        query = """
        MATCH (p:Character {id: $id})-[r]->(i:Item)
        WHERE type(r) = 'OWNS'
        RETURN i.id as id, i.name as name, labels(i) as labels, i
        """
        items = []
        with self.driver.session() as session:
            result = session.run(query, id=pid)
            for record in result:
                props = dict(record['i'])
                # Determine type from labels if possible, else default
                itype = "Item"
                if "Weapon" in record['labels']: itype = "Weapon"
                elif "Armor" in record['labels']: itype = "Armor"
                
                items.append({
                    "id": record['id'],
                    "name": record['name'],
                    "type": itype,
                    "properties": props
                })
        return items

    def purchase_item(self, session_id: str, item_id: str) -> Dict[str, Any]:
        pid = "player_main"
        
        # Transaction: Check cost -> Deduct -> Own
        # We assume item has a 'value' property string like "50gp" or int 50
        # For simplicity, we'll try to parse int, or default to 10 if missing
        
        with self.driver.session() as session:
            # 1. Get current gold and item value
            check_query = """
            MATCH (p:Character {id: $pid}), (i:Item {id: $iid})
            RETURN p.gold as gold, i.value as value, i.name as name
            """
            res = session.run(check_query, pid=pid, iid=item_id).single()
            if not res:
                return {"success": False, "message": "Player or Item not found."}
            
            gold = res['gold']
            val_str = str(res['value'])
            # simple parse: remove 'gp' and int()
            try:
                cost = int(''.join(filter(str.isdigit, val_str)))
            except:
                cost = 10 # Default fallback
                
            if gold < cost:
                return {"success": False, "message": f"Insufficient funds. Cost: {cost}, Bal: {gold}"}
            
            # 2. Execute Purchase
            buy_query = """
            MATCH (p:Character {id: $pid}), (i:Item {id: $iid})
            SET p.gold = p.gold - $cost
            MERGE (p)-[:OWNS {acquired_at: datetime()}]->(i)
            RETURN p.gold as new_balance
            """
            session.run(buy_query, pid=pid, iid=item_id, cost=cost)
            
            return {"success": True, "message": f"Purchased {res['name']} for {cost}gp", "new_balance": gold - cost}

    def sell_item(self, session_id: str, item_id: str) -> Dict[str, Any]:
        """
        Sells an item owned by the player.
        Logic: Verify ownership -> Remove relationship -> Add Gold (50% value).
        """
        pid = "player_main"
        
        with self.driver.session() as session:
            # 1. Verify Ownership and Get Value
            # Use WHERE type(r) = 'OWNS' to avoid Neo4j warning if type missing
            check_query = """
            MATCH (p:Character {id: $pid})-[r]->(i:Item {id: $iid})
            WHERE type(r) = 'OWNS'
            RETURN p.gold as gold, i.value as value, i.name as name
            """
            res = session.run(check_query, pid=pid, iid=item_id).single()
            if not res:
                return {"success": False, "message": "You don't own this item."}
            
            gold = res['gold']
            val_str = str(res['value'])
            try:
                base_value = int(''.join(filter(str.isdigit, val_str)))
            except:
                base_value = 10
            
            sell_value = int(base_value * 0.5) # Sell for 50%
            
            # 2. Execute Sell
            sell_query = """
            MATCH (p:Character {id: $pid})-[r]->(i:Item {id: $iid})
            WHERE type(r) = 'OWNS'
            DELETE r
            SET p.gold = p.gold + $sell_value
            RETURN p.gold as new_balance
            """
            session.run(sell_query, pid=pid, iid=item_id, sell_value=sell_value)
            
            return {
                "success": True, 
                "message": f"Sold {res['name']} for {sell_value}gp", 
                "gold_gained": sell_value,
                "new_balance": gold + sell_value
            }
