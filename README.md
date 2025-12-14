# A.R.C.A.N.A.
**Agentic Rules-based & Creative Autonomous Narrative Architecture**

"Erudite Automaton" – A fully autonomous AI Dungeon Master (DM) for D&D 5e.

---

## 📚 Table of Contents
- [Code Structure](#-code-structure)
- [Installation](#-installation)
- [Environment Setup](#-environment-setup)
- [Usage & Demonstrations](#-usage--demonstrations)
- [Reproducible Experiments](#-reproducible-experiments)
- [Architecture](#-architecture)
- [Data Monitoring](#-data-monitoring)
- [Troubleshooting](#-troubleshooting)

---

## 📂 Code Structure

The project is divided into a Python-based backend (FastAPI + LangGraph) and a Next.js frontend.

```text
/
├── backend/                  # Core Logic
│   ├── app/
│   │   ├── agents/           # AI Agents (Orchestrator, Narrative, Rules, World)
│   │   ├── api/              # FastAPI Routes (Play, Debug)
│   │   ├── memory/           # Hybrid Memory (Neo4j + Vector Store)
│   │   ├── models/           # Pydantic Schemas
│   │   └── rules/            # Rules Adjudication Engine
│   └── scripts/              # Utility scripts (Seeding, Testing)
├── frontend/                 # UI
│   ├── app/                  # Next.js App Router Pages
│   └── components/           # React Components (CombatLog, InventoryPanel)
├── data/                     # Data Storage
│   ├── rules/                # D&D 5e Rules Data (JSON)
│   └── story/                # Story Modules
├── scripts/                  # Root-level experiment scripts
└── docker-compose.yml        # Infrastructure Definition
```

---

## 🚀 Installation

### 1. Prerequisites
*   **Docker Desktop**: Must be installed and running.
*   **Google Gemini API Key**: Obtain one from [Google AI Studio](https://aistudio.google.com/).

### 2. Setup
Run the startup script to initialize your environment file.

```bash
chmod +x start.sh
./start.sh
```

**Note**: The script will likely pause or fail the first time because your API key is missing.

### 3. Run the Application
Start the entire stack (Backend + Frontend + Neo4j):

```bash
./start.sh
```

*   **Frontend**: [http://localhost:3000](http://localhost:3000)
*   **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Neo4j Browser**: [http://localhost:7474](http://localhost:7474)

### 4. Seed the World (Required)
The database starts empty. Populate it with initial locations, NPCs, and relationships:

```bash
docker-compose exec backend python -m app.scripts.seed
```

---

## ⚙️ Environment Setup

The project uses a `.env` file in the root directory.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `GOOGLE_API_KEY` | **Required.** Your Gemini API Key. | None |
| `NEO4J_URI` | Address of the Neo4j database. | `bolt://neo4j:7687` |
| `NEO4J_USER` | Database username. | `neo4j` |
| `NEO4J_PASSWORD` | Database password. | `password` |
| `LLM_MODEL_NAME` | Model to use for generation. | `gemini-1.5-pro` |

---

## 🎮 Usage & Demonstrations

### Web Interface
Navigate to [http://localhost:3000](http://localhost:3000).
1.  Click **"Start Adventure"**.
2.  Type actions like *"I look around"* or *"I attack the goblin"*.
3.  View your **Inventory** and **Stats** updating in real-time.

### API Usage
You can interact directly with the backend via HTTP.

**Start a Session:**
```bash
curl -X POST "http://localhost:8000/api/play/start_session" \
     -H "Content-Type: application/json" \
     -d '{}'
```

**Take an Action:**
```bash
curl -X POST "http://localhost:8000/api/play/step" \
     -H "Content-Type: application/json" \
     -d '{
           "session_id": "YOUR_SESSION_ID",
           "text": "I attack the goblin with my sword!"
         }'
```

---

## 🧪 Reproducible Experiments

We provide scripts to verify the core mechanics of the system, specifically the Combat Flow.

### Experiment: Combat Flow Verification
This experiment tests the end-to-end flow of:
1.  Initializing a session.
2.  Retrieving the current state.
3.  Processing a combat action ("I attack...").
4.  Verifying that the `action_log` (combat resolution) is generated.

**Run the Experiment:**
Ensure the stack is running (`./start.sh`), then run:

```bash
python scripts/test_combat_flow.py
```

**Expected Output:**
```text
1. Starting Session...
Session ID: ...
2. Sending Attack Command...
Response received.
[SUCCESS] Action Log Found:
[
  {
    "type": "attack",
    "description": "...",
    "damage": ...
  }
]
```

---

## 🏗️ Architecture

*   **OrchestratorAgent**: Manages the game loop, detects user intent, and delegates tasks.
*   **NarrativeAgent**: Generates immersive story text using Google Gemini.
*   **RulesLawyerAgent**: Adjudicates actions based on D&D 5e rules.
*   **Memory System**:
    *   **Episodic**: Vector Store (Chroma) for narrative history.
    *   **Semantic**: Temporal Knowledge Graph (Neo4j) for game state (HP, Inventory, Locations).

---

## 🛠️ Data Monitoring

Visualize the game world and memory in the Neo4j Browser.

1.  Go to [http://localhost:7474](http://localhost:7474)
2.  Login with `neo4j` / `password`.
3.  Run this query to see the entire graph:
    ```cypher
    MATCH (n) RETURN n
    ```

---

## 🐛 Troubleshooting

| Issue | Solution |
| :--- | :--- |
| **API Key Error** | Check `.env` file and ensure `GOOGLE_API_KEY` is set. Restart containers. |
| **Database Empty** | Run the seed command: `docker-compose exec backend python -m app.scripts.seed` |
| **Connection Refused** | Ensure Docker containers are running: `docker-compose ps` |
| **Frontend/Backend Logs** | View logs: `docker-compose logs -f backend` or `frontend` |
| **Rebuild Required** | If you changed `requirements.txt`: `docker-compose up --build` |
