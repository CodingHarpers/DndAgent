# A.R.C.A.N.A.
**Agentic Rules-based & Creative Autonomous Narrative Architecture**

"Erudite Automaton" – A fully autonomous AI Dungeon Master (DM) for D&D 5e.

## 🚀 Quick Start

### 1. Prerequisites
*   **Docker Desktop** (running)
*   **Google Gemini API Key** (from [Google AI Studio](https://aistudio.google.com/))

### 2. Setup Environment
The first time you run the start script, it will generate a `.env` file for you.

```bash
chmod +x start.sh
./start.sh
```

**STOP!** The script will pause or fail if the API key is missing.
Open the newly created `.env` file in the root directory and paste your key:

```bash
# .env
GOOGLE_API_KEY=your_actual_api_key_here
```

### 3. Run the Project
Start the entire stack (Backend + Frontend + Neo4j):

```bash
./start.sh
```

*   **Frontend**: [http://localhost:3000](http://localhost:3000)
*   **Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Neo4j Browser**: [http://localhost:7474](http://localhost:7474)

### 4. Seed the World (Important!)
The database starts empty. To populate it with the initial world (Locations, NPCs, Factions), run:

```bash
docker-compose exec backend python -m app.scripts.seed
```

You should see output indicating that Locations, NPCs, and Relationships have been added.

## 🛠️ Data Monitoring (Neo4j)

You can visualize the game world and memory in the Neo4j Browser.

1.  Go to [http://localhost:7474](http://localhost:7474)
2.  **Login**:
    *   Username: `neo4j`
    *   Password: `password` (default)
3.  **Run Query**:
    To see the entire graph:
    ```cypher
    MATCH (n) RETURN n
    ```

## 🏗️ Architecture

*   **Backend**: Python (FastAPI, LangGraph)
    *   `OrchestratorAgent`: Manages game loop.
    *   `NarrativeAgent`: Generates story text using Google Gemini.
    *   `RulesLawyerAgent`: Handles game mechanics.
    *   `Memory`: Hybrid system with Vector Store (Chroma) and Knowledge Graph (Neo4j).
*   **Frontend**: Next.js (TypeScript, Tailwind)
*   **Infrastructure**: Docker Compose

## 🐛 Debugging

*   **Frontend Logs**: `docker-compose logs -f frontend`
*   **Backend Logs**: `docker-compose logs -f backend`
*   **Rebuild**: If you change dependencies (requirements.txt or package.json), run `./start.sh` again to rebuild.
