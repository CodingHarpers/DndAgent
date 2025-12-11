from neo4j import GraphDatabase
import random
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
        query = (
            f"MERGE (n:{label} {{id: $id}}) "
            "SET n += $props"
        )
        with self.driver.session() as session:
            # Pydantic models need explicit conversion to dict for Neo4j driver
            props = entity.properties.model_dump(exclude_unset=True)
            session.run(query, id=entity.id, props=props)

    def add_relationship(self, rel: RelationshipEdge):
        # Sanitize type by wrapping in backticks
        rel_type = f"`{rel.type}`"
        query = (
            "MATCH (a {id: $source_id}), (b {id: $target_id}) "
            f"MERGE (a)-[r:{rel_type}]->(b) "
            "SET r += $props"
        )
        with self.driver.session() as session:
            # Pydantic models need explicit conversion to dict for Neo4j driver
            props = rel.properties.model_dump(exclude_unset=True)
            session.run(query, source_id=rel.source_id, target_id=rel.target_id, props=props)

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
            # 1. Get current gold and item value
            # Standardize invalid inputs
            search_term = item_id.strip()
            
            # Tokenize for flexible matching (e.g. "healing potion" -> matches "Potion of Healing")
            # We filter out short words to avoid noise if needed, but for now simple split is fine.
            tokens = [t.lower() for t in search_term.split() if len(t) > 2]
            if not tokens: # Fallback if only short words
                tokens = [search_term.lower()]

            # Cypher query: Find item where ALL tokens are present in the name (case-insensitive)
            find_query = """
            MATCH (p:Character {id: $pid})
            OPTIONAL MATCH (i:Item)
            WHERE i.id = $iid OR 
                  (size($tokens) > 0 AND all(token IN $tokens WHERE toLower(i.name) CONTAINS token))
            WITH p, i
            ORDER BY size(i.name) ASC 
            LIMIT 1
            RETURN p.gold as gold, i.value as value, i.name as name, i.id as found_id
            """
            
            res = session.run(find_query, pid=pid, iid=item_id, tokens=tokens).single()
            
            if not res or not res['found_id']:
                return {"success": False, "message": f"Item '{item_id}' not found."}
            
            gold = res['gold']
            actual_item_id = res['found_id']
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
            session.run(buy_query, pid=pid, iid=actual_item_id, cost=cost)
            
            return {"success": True, "message": f"Purchased {res['name']} for {cost}gp", "new_balance": gold - cost}

    def sell_item(self, session_id: str, item_id: str) -> Dict[str, Any]:
        """
        Sells an item owned by the player.
        Logic: Verify ownership -> Remove relationship -> Add Gold (50% value).
        """
        pid = "player_main"
        
        with self.driver.session() as session:
            # 1. Verify Ownership and Get Value
            # 1. Verify Ownership and Get Value
            search_term = item_id.strip()
            tokens = [t.lower() for t in search_term.split() if len(t) > 2]
            if not tokens:
                tokens = [search_term.lower()]

            check_query = """
            MATCH (p:Character {id: $pid})-[r:OWNS]->(i:Item)
            WHERE i.id = $iid OR 
                  (size($tokens) > 0 AND all(token IN $tokens WHERE toLower(i.name) CONTAINS token))
            WITH p, i, r
            LIMIT 1
            RETURN p.gold as gold, i.value as value, i.name as name, i.id as found_id, elementId(r) as rid
            """
            res = session.run(check_query, pid=pid, iid=item_id, tokens=tokens).single()
            
            if not res:
                return {"success": False, "message": f"You don't own '{item_id}'."}
            
            gold = res['gold']
            actual_item_id = res['found_id']
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
            session.run(sell_query, pid=pid, iid=actual_item_id, sell_value=sell_value)
            
            return {
                "success": True, 
                "message": f"Sold {res['name']} for {sell_value}gp", 
                "gold_gained": sell_value,
                "new_balance": gold + sell_value
            }

    def roll_dice(self, sides: int, times: int = 1) -> int:
        return sum(random.randint(1, sides) for _ in range(times))

    def attack(self, session_id: str, target_id: str) -> Dict[str, Any]:
        """
        Executes an attack from the player to a target.
        """
        pid = "player_main"

        with self.driver.session() as session:
            # 1. Get Attacker and Target Stats
            # We assume target is a Character or Enemy node
            query_stats = """
            MATCH (p:Character {id: $pid})
            OPTIONAL MATCH (t {id: $tid})
            RETURN p, t, labels(t) as t_labels
            """
            res = session.run(query_stats, pid=pid, tid=target_id).single()
            
            if not res or not res['t']:
                return {"success": False, "message": "Target not found."}
            
            player = dict(res['p'])
            target = dict(res['t'])
            target_labels = res['t_labels'] or []

            # Check if target is alive
            if target.get('hp_current', 0) <= 0:
                 return {"success": False, "message": "Target is already defeated."}

            # 2. Combat Calculation (2d6 System)
            # Hit Check: 2d6 vs Target Defense (or default 10)
            roll_1 = self.roll_dice(6)
            roll_2 = self.roll_dice(6)
            attack_roll = roll_1 + roll_2
            
            # Simple defense stat or default to 10
            target_defense = target.get('defense', 10)
            
            hit = attack_roll >= target_defense
            
            damage = 0
            if hit:
                # Damage Roll: Weapon Die (default d6) + Power Mod
                # Simplify: just use d6 + power/3 for now or similar
                # User asked for weapon-based dice, let's look for equipped weapon
                # For MVP, let's just assume a d8 base damage + power bonus (e.g. power-10)
                power_bonus = max(0, (player.get('power', 10) - 10) // 2)
                damage = self.roll_dice(8) + power_bonus
                
                # Apply Damage
                new_hp = target.get('hp_current', 10) - damage
                
                update_query = """
                MATCH (t {id: $tid})
                SET t.hp_current = $new_hp
                MERGE (p:Character {id: $pid})
                MERGE (p)-[r:ATTACKED {
                    roll: $roll,
                    damage: $damage,
                    hit: $hit,
                    timestamp: datetime()
                }]->(t)
                RETURN t.hp_current
                """
                session.run(update_query, tid=target_id, pid=pid, new_hp=new_hp, roll=attack_roll, damage=damage, hit=hit)
            else:
                 # Log Miss
                log_query = """
                MATCH (t {id: $tid}), (p:Character {id: $pid})
                MERGE (p)-[r:ATTACKED {
                    roll: $roll,
                    damage: 0,
                    hit: $hit,
                    timestamp: datetime()
                }]->(t)
                """
                session.run(log_query, tid=target_id, pid=pid, roll=attack_roll, hit=hit)

            return {
                "success": True,
                "hit": hit,
                "roll": attack_roll,
                "damage": damage,
                "target_id": target_id,
                "target_hp": target.get('hp_current', 10) - damage if hit else target.get('hp_current', 10),
                "message": f"Attacked {target.get('name', 'Enemy')}. Roll: {attack_roll} (Target: {target_defense}). {'HIT' if hit else 'MISS'} for {damage} dmg."
            }
