You are an expert AI engineer and game systems architect. Build a **codebase** for the project:

A.R.C.A.N.A.: Agentic Rules-based & Creative Autonomous Narrative Architecture  
“Erudite Automaton” – a fully autonomous AI Dungeon Master (DM) for D&D 5e, with:
- Multi-agent orchestration (Narrative, Rules Lawyer, World-Builder, Orchestrator)
- Hybrid memory (episodic vector store + semantic Temporal Knowledge Graph)
- Rule-grounded adjudication via a RuleRAG-style neuro-symbolic component
- A minimal web UI to play a short AI-moderated scenario and inspect memory

## HIGH-LEVEL REQUIREMENTS

1. **Multi-Agent System**
   - Use **Python** for backend.
   - Use **LangGraph** for multi-agent orchestration and state management.
   - Define at least these agents:
     - `OrchestratorAgent`: coordinates everything, routes requests to other agents.
     - `NarrativeAgent`: generates narrative scenes and dialogue in constrained style.
     - `RulesLawyerAgent`: performs rule-grounded adjudication using a structured rules DB and RAG.
     - `WorldBuilderAgent`: updates world state, locations, NPCs, and creates encounters/loot.
   - Agents must pass **structured JSON messages** between each other, not just plain text.

2. **Memory & Retrieval Subsystem (Agent Memory)**
   - Dual-memory design:
     - **Episodic Memory**:
       - Vector-based store of narrative events and logs.
       - Use **FAISS** or **Chroma** as the vector store (embed with an OpenAI-compatible embedding model).
       - Store: `session_id`, `timestamp`, `speaker`, `event_type`, `summary`, `raw_text`, `embedding`.
     - **Semantic Temporal Knowledge Graph (TKG)**:
       - Use **Neo4j** as the backing store via the official Python driver.
       - Encodes entities (PCs, NPCs, locations, items, quests) and relations with timestamps.
       - Example node/edge types: `Character`, `Location`, `Item`, `Quest`, `RELATION(type, since, until, provenance)`.
   - **Hybrid retrieval:**
     - Implement a `HybridRetriever` that combines:
       - Dense retrieval (vector similarity from FAISS/Chroma).
       - Sparse retrieval (BM25 via **Meilisearch** or **Elasticsearch**, choose one, with a thin wrapper).
     - Support query types:
       - “episodic recall” (retrieve past narrative turns relevant to the current context).
       - “world facts” (query TKG for current canonical facts).
       - “temporal queries” (e.g., “What happened in session 3 at the manor?”).
   - Implement a `MemoryRouter` that:
     - Receives agent queries (from Orchestrator)
     - Routes to episodic vs semantic memory (or both)
     - Returns a unified, ranked context bundle.

3. **RuleRAG / Rules Lawyer Agent**
   - Implement a **neuro-symbolic rule pipeline**:
     - A **rules corpus** for D&D 5e Combat (PHB Chapter 9 subset) stored as JSON or YAML:
       - Example schema: `rule_id`, `title`, `section`, `tags`, `prerequisites`, `effects`, `exceptions`, `source_ref`.
     - A `RulesIndex` that:
       - Builds a vector index over rule texts.
       - Provides lexical BM25 search.
     - A `RulesLawyerEngine` that:
       - Given a rules question + context (e.g., “Can this character use Sneak Attack now?”) retrieves candidate rules, runs them through an LLM, and outputs:
         - `decision` (e.g., ALLOWED / DENIED / ROLL_CHECK)
         - `required_rolls` (e.g., attack roll, saving throw, skill checks)
         - `explanation` in natural language
         - `applied_rules` (IDs referencing the rules DB)
   - Scaffold a **HITL pipeline** for rule extraction:
     - A script that:
       - Takes raw rule text snippets.
       - Uses an LLM to propose structured JSON rule entries.
       - Marks entries as `draft` until manually approved (for now just stub this approval step).
   - Include basic **unit tests** for:
     - Rules retrieval (by keyword and tag).
     - A couple of hard-coded scenarios (e.g., advantage/disadvantage, opportunity attack).

4. **Narrative & World Model**
   - Define a standard JSON schema for **Scenes**:
     - `scene_id`, `title`, `narrative_text`, `location`, `characters_present`, `world_state_diff`, `available_actions`, `metadata`.
   - The `NarrativeAgent`:
     - Takes current scene + memory context + player input.
     - Outputs a new `Scene` JSON and corresponding nicely formatted prose for the player.
   - The `WorldBuilderAgent`:
     - Maintains higher-level world state:
       - Locations, NPCs, factions, quest states.
     - Updates the TKG (via APIs) based on scene consequences.
     - Can programmatically generate:
       - Simple dungeon rooms
       - Basic encounters (enemy list + CR-like difficulty score)
       - Loot tables.
   - The **Orchestrator**:
     - Main flow:
       1. Parse player input into structured intent (via LLM or simple heuristic).
       2. Query `MemoryRouter` for episodic + world context.
       3. Ask `RulesLawyerAgent` if any mechanical adjudication is required (e.g., skill checks, combat).
       4. Ask `NarrativeAgent` to generate the next `Scene`.
       5. Ask `WorldBuilderAgent` to update world state + TKG.
       6. Persist new events in episodic memory.
       7. Return structured scene + prose to the frontend.

5. **Backend Tech Stack & Structure**

Use **Python 3.11+** with:

- **FastAPI** as the web framework.
- **LangGraph** for multi-agent orchestration.
- FAISS or Chroma for dense vector store.
- Meilisearch or Elasticsearch for BM25.
- Neo4j for TKG.
- `pydantic` models for all internal schemas.
- `pytest` for tests.
- `uvicorn` for dev server.
- OpenAI-compatible LLM client (e.g., `openai` or similar) but abstract behind an interface (so models can be swapped later).

Root-level backend structure (you should generate the actual files):

- `backend/`
  - `app/main.py` – FastAPI entry point.
  - `app/config.py` – settings (env-based) for DB URLs, API keys, model names, etc.
  - `app/models/schemas.py` – Pydantic models for Scene, MemoryRecord, RuleEntry, AgentMessages, etc.
  - `app/agents/orchestrator.py`
  - `app/agents/narrative_agent.py`
  - `app/agents/rules_lawyer_agent.py`
  - `app/agents/world_builder_agent.py`
  - `app/memory/episodic_store.py`
  - `app/memory/semantic_tkg.py`
  - `app/memory/router.py`
  - `app/retrieval/hybrid_retriever.py`
  - `app/rules/rules_index.py`
  - `app/rules/rules_lawyer_engine.py`
  - `app/rules/rule_extraction_pipeline.py`
  - `app/services/llm_client.py` – abstraction over LLM/embedding providers.
  - `app/api/routes_play.py` – endpoints for the UI (start session, send player input, get scene).
  - `app/api/routes_debug.py` – endpoints to inspect memory and rules.
  - `tests/` – pytest tests for memory, retrieval, and rules adjudication.
  - `Dockerfile`
- Root:
  - `docker-compose.yml` (spin up backend, Neo4j, vector store, and search engine).
  - `README.md`
  - `docs/architecture.md` – high-level architecture diagram + flows (you can stub the diagram as markdown text).

6. **Frontend / MVP UI**

Implement a simple but clean **TypeScript + Next.js + Tailwind** frontend:

- Tech stack:
  - **Next.js (App Router)**, **TypeScript**
  - **TailwindCSS**
  - Optional: **shadcn/ui** for components
- Structure:

  - `frontend/`
    - `app/layout.tsx`
    - `app/page.tsx` – landing page.
    - `app/play/page.tsx` – main play interface.
    - `app/debug/memory/page.tsx` – memory inspector view.
    - `components/ChatPanel.tsx` – player input + messages display.
    - `components/SceneViewer.tsx` – shows current scene JSON + formatted prose.
    - `components/MemoryTimeline.tsx` – shows episodic events over time.
    - `components/WorldStateView.tsx` – basic view for TKG facts relevant to the current scene.
  - Integrate with backend via REST endpoints (`/api/play/*`, `/api/debug/*`).
  - Features:
    - Start new session, resume session.
    - Show current scene text + a list of suggested actions.
    - Let the user type arbitrary actions as well.
    - Debug views to show which memories and rules were retrieved for each response.

7. **Procedural Plan (What I Want You To Do)**
Follow this sequence when generating the codebase:

1. **Repository Planning**
   - Propose and print the full repo structure (root, backend, frontend, docs, tests).
   - Ensure it matches the components listed above (or improves them slightly while keeping the same spirit).

2. **Backend Scaffolding**
   - Initialize `backend` with FastAPI app, config, and dependency wiring.
   - Implement Pydantic schemas for Scenes, Memory Records, Rules, and Agent messages.
   - Set up LangGraph with minimal placeholder nodes for each agent and an orchestrator graph.
   - Expose basic REST endpoints:
     - `POST /api/play/start_session`
     - `POST /api/play/step` (player input → next scene)
     - `GET /api/debug/session/{id}/memory`
     - `GET /api/debug/session/{id}/world_state`

3. **Memory & Retrieval Implementation**
   - Implement episodic store (FAISS/Chroma).
   - Implement TKG wrapper for Neo4j.
   - Implement HybridRetriever and MemoryRouter with dense + BM25 retrieval.
   - Add unit tests for these components.

4. **Rules Lawyer & RuleRAG Scaffolding**
   - Implement a minimal rules corpus (a few combat rules hard-coded as JSON).
   - Implement RulesIndex + RulesLawyerEngine.
   - Add endpoints and tests for:
     - `POST /api/debug/rules/query` – query rules and see the decision + explanation.

5. **Narrative & World Agents**
   - Implement simple versions of NarrativeAgent and WorldBuilderAgent that:
     - Use the LLM client abstraction.
     - Respect the Scene JSON schema.
     - Write to episodic memory and TKG via provided APIs.

6. **Frontend**
   - Scaffold Next.js + Tailwind app in `frontend/`.
   - Create `/play` page with chat-like UI.
   - Create `/debug/memory` page that can show session memories and world facts using backend endpoints.

7. **Documentation & DX**
   - Fill in `README.md` with:
     - Quickstart (docker-compose up).
     - How to set environment variables (LLM keys, DB URLs).
     - Example walkthrough of a single player turn.
   - Fill in `docs/architecture.md` with:
     - Textual description of data flows between agents, memory, and frontend.
     - Sequence of steps for “player action → orchestrator → agents → updated scene”.

8. **Code Quality**
   - Prefer clear, modular code over over-optimisation.
   - Add docstrings to public classes and functions.
   - Provide a few example curl/HTTP calls in the README for manual testing.
   - Make sure the project can run with `docker-compose up` plus a minimal `.env` file.

Here is the API key in case you need it AQ.Ab8RN6JU86oVVdvogK7mAwlSVOfUroMyeV0n2MTP9WDiWUY_Zg. Your job is to create a **coherent, working skeleton** that demonstrates the core architecture and runs end-to-end for a simple mock D&D interaction.

Start by printing the proposed repo tree and then proceed to implement the code.