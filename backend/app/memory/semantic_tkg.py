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
        query = (
            f"MERGE (n:{entity.label} {{id: $id}}) "
            "SET n += $props"
        )
        with self.driver.session() as session:
            session.run(query, id=entity.id, props=entity.properties)

    def add_relationship(self, rel: RelationshipEdge):
        query = (
            "MATCH (a {id: $source_id}), (b {id: $target_id}) "
            f"MERGE (a)-[r:{rel.type}]->(b) "
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
