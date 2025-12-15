# Technical Presentation Script: A.R.C.A.N.A.

*(Speaker Note: This script is designed to accompany the three technical slides: System Overview, Technical Innovations, and Technical Breakdown.)*

---

## Slide: System Overview

"At a high level, A.R.C.A.N.A. isn't just a chatbot; it is a **Multi-Agent System** orchestrated by a LangGraph state machine. We moved away from the fragile 'single prompt' approach and instead decomposed the Dungeon Master's responsibilities into specialized agents."

"You can see our diverse cast of agents here:"

1.  **The Orchestrator:** This is the brain. It manages the state loop and routes tasks. It decides *who* needs to act—does the user need a story description, a rule judgment, or a world update?
2.  **The Narrative Agent:** This is our creative director. It focuses purely on generating immersive prose and identifying safety constraints, without worrying about math.
3.  **The Rules Lawyer:** This agent implements our **RuleRAG** system. It consults a symbolic knowledge base to provide explicit, explainable rulings—like a Supreme Court judge for D&D.
4.  **The World Builder:** This is our state manager. It maintains the physical reality of the game—grid locations, HP, and inventory—updating our Knowledge Graph.
5.  **The Memory Router:** A hybrid system that decides whether to fetch past narrative logs (Episodic) or current facts (Semantic) like 'Where is the key?'"

---

## Slide: Technical Innovations

"We want to highlight five key technical innovations that make this architecture novel."

**1. Multi-Agent DM Decomposition**
"As I mentioned, we treat the DM not as a persona, but as a *department*. Agents negotiate via conversational protocols—similar to AutoGen—allowing specialized sub-brains to handle conflict resolution and validation."

**2. RuleRAG & Neuro-Symbolic Reasoning**
"This is a major differentiator. We don't rely on the LLM's training data for rules, which leads to hallucinations. Instead, we extracted symbolic rules from the D&D 5e SRD into a structured knowledge base. We use **Neuro-Symbolic Reasoning** to combine the flexibility of the LLM with the rigidity of these constraints, ensuring legal actions and precise calculations."

**3. Dual-Memory Architecture**
"We implemented a cognitive architecture inspired by human memory:"
*   **Episodic Memory (Vector DB):** We use Chroma to store unstructured logs with timestamps. This lets the agent recall *events*, like 'The time I fought the dragon.'
*   **Semantic Memory (Knowledge Graph):** We use Neo4j to store *facts*. This ensures that if you steal a key, the graph updates the 'OWNS' relationship instantly.

**4. Word2World-Inspired Narrative Loop**
"Our 'World Builder' agent listens to the freeform story and converts it into structured JSON updates. If the narrator describes a 'roaring fireplace,' the World Builder instantiates a `Fireplace` object in the valid location."

**5. Map & Combat Logic**
"Finally, we support grid-based reasoning. We don't just 'imagine' distances; the TKG explicitly tracks positions to validate range, line-of-sight, and opportunity attacks."

---

## Slide: Technical Breakdown

"To summarize how these pieces come together in practice, we can look at our three core pillars:"

**1. Storytelling (Narrative Agent)**
"This is the **User Interface**. Powered by Gemini 1.5 Pro, it separates 'Flavor' from 'Mechanics.' It doesn't track numbers; it focuses entirely on the immersion, acting as the Creative Director."

**2. RuleRAG (Rules Lawyer)**
"This is the **Impartial Judge**. utilizing a RAG pipeline with ChromaDB and Gemini 2.5 Flash. It provides 'Proactive Adjudication'—fetching exact mechanics to formulate logic for the DM to execute, rather than guessing."

**3. Memory (Temporal Knowledge Graph)**
"This is the **Accountant**. Powered by Neo4j, it provides the 'World State.' By choosing a Graph Database over a Vector store for state, we ensure that inventory, health, and relationships are perfectly consistent. No more 'dream logic' where items disappear."

---

## Memory Architecture Design (Report)

The memory subsystem of A.R.C.A.N.A. employs a dual-memory architecture inspired by cognitive science models of human memory, specifically distinguishing between episodic and semantic memory systems. The episodic memory component is implemented using ChromaDB's persistent vector database, which stores narrative logs as high-dimensional embeddings (1536 dimensions) generated through OpenAI's text-embedding-3-small model. Each memory record encapsulates structured metadata including session identifiers, ISO-formatted timestamps, speaker attribution, event types (e.g., "dialogue", "action", "system"), textual summaries, and raw narrative text. During retrieval, the system performs semantic similarity search by embedding user queries and computing cosine similarity against stored vectors, enabling contextual event recall such as "the time the player fought the dragon"—demonstrating the system's ability to surface temporally-grounded narrative sequences through approximate semantic matching rather than exact keyword lookup. Conversely, the semantic memory component is architected as a Temporal Knowledge Graph (TKG) using Neo4j, implementing an entity-relationship model where nodes represent game entities (typed as Character, Item, Weapon, Armor, Location) with structured property schemas, and edges represent typed relationships (OWNS, ATTACKED, LOCATED_IN) with temporal and contextual metadata. The graph operations leverage Cypher query language with transactional guarantees: MERGE operations ensure idempotent entity creation, MATCH-SET patterns enable atomic property updates, and relationship deletion maintains referential integrity. For instance, when inventory management occurs, the system executes multi-step transactional queries that verify ownership, compute financial transactions (with gold deduction/addition), and atomically update OWNS relationships with temporal markers (acquired_at timestamps), all within a single Neo4j session transaction—preventing race conditions and ensuring ACID compliance. The graph schema extends beyond passive storage to actively encode game mechanics: character statistics (hp_current, hp_max, power, speed, gold) are stored as node properties, combat interactions generate ATTACKED edges with roll values and damage calculations, and spatial relationships enable pathfinding queries for movement validation. The Memory Router implements a hybrid retrieval mechanism that queries both systems in parallel: episodic retrieval filters by session_id and performs k-nearest-neighbor vector search (default k=5) to return semantically relevant narrative contexts, while semantic retrieval extracts entity identifiers from queries to traverse relationship graphs via Cypher MATCH patterns, returning structured fact sets (e.g., related entities and their connection types). The architectural separation reflects a fundamental design philosophy: episodic memory handles the *qualitative* aspects of gameplay (narrative flow, emotional context, story coherence) through fuzzy semantic matching, while semantic memory handles the *quantitative* aspects (inventory state, health points, spatial coordinates, ownership) through exact graph operations. This design choice prioritizes referential integrity and transactional consistency for state-critical operations—whereas vector databases excel at similarity search, they lack the transactional semantics required for financial calculations (gold transactions), combat resolution (hp updates), and relationship management (ownership transfers). By implementing state management in Neo4j rather than relying on LLM-internal representations or vector stores, the system eliminates "dream logic" phenomena where items mysteriously disappear, health points become inconsistent, or relationships contradict previous states—ensuring that the game world maintains a queryable, verifiable, and coherent state throughout extended gameplay sessions, with the ability to reconstruct historical state through graph traversal and temporal relationship properties.
