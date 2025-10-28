# A.R.C.A.N.A. Project Instructions

**Agentic Rules-based & Creative Autonomous Narrative Architecture**

This document provides a detailed guide on how to set up, understand, and develop the A.R.C.A.N.A. project. It is intended for teammates joining the project.

## 🚀 Quick Start Guide

### 1. Prerequisites
*   **Docker Desktop**: Must be installed and running.
*   **Google Gemini API Key**: Required for the LLM agents.

### 2. Initial Setup
1.  **Clone the repository**.
2.  **Generate Environment Config**:
    Run the start script once to generate the `.env` file.
    ```bash
    chmod +x start.sh
    ./start.sh
    ```
    *Note: The script will likely pause/fail initially because the API key is missing.*

3.  **Configure API Key**:
    Open `.env` in the root directory `DndAgent/` and add your key:
    ```bash
    GOOGLE_API_KEY=your_actual_api_key_here
    ```

### 3. Running the Application
Start the full stack (Frontend, Backend, Database):
```bash
./start.sh
```
*   **Frontend**: [http://localhost:3000](http://localhost:3000)
*   **Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Neo4j Browser**: [http://localhost:7474](http://localhost:7474) (User: `neo4j`, Pass: `password`)

### 4. Seeding the World
**Critical Step**: The database starts empty. You must seed it with initial locations, NPCs, and items.
Run this command in a new terminal window while the app is running:
```bash
docker-compose exec backend python -m app.scripts.seed
```

---

## 🏗️ Project Architecture & Workflow

The system is designed as an agentic loop where a central Orchestrator manages the flow of information between the user, the narrative LLM, and the game state (Neo4j).

### Directory Structure

#### Backend (`/backend`)
Built with **FastAPI** and **Python**.
*   **`app/main.py`**: The entry point for the API.
*   **`app/agents/orchestrator.py`**: The core brain. It manages the game loop, detects user intent, and coordinates other agents.
*   **`app/agents/narrative_agent.py`**: Wraps the LLM to generate story text.
*   **`app/agents/world_builder_agent.py`**: Interface for modifying the world state.
*   **`app/memory/semantic_tkg.py`**: The "Temporal Knowledge Graph" (TKG). It interacts directly with **Neo4j** to store RPG stats (Health, Gold), Inventory, and Relationships.
*   **`app/api/routes_play.py`**: API endpoints used by the frontend.

#### Frontend (`/frontend`)
Built with **Next.js**, **TypeScript**, and **Tailwind CSS**.
*   **`app/play/page.tsx`**: The main game interface. Handles:
    *   Starting a session.
    *   Sending user actions.
    *   Displaying the narrative feed.
    *   Updating the Stats and Inventory panels.
*   **`components/StatsPanel.tsx`**: Visualizes player health, gold, and stats.
*   **`components/InventoryPanel.tsx`**: Displays items and handles Buy/Sell/Equip interactions.

### The Game Loop Workflow

1.  **User Input**: The user types an action (e.g., "I attack the goblin" or "Buy the sword") in the frontend.
2.  **API Call**: Frontend sends this to `POST /api/play/step`.
3.  **Context Retrieval**:
    *   `Orchestrator` fetches current RPG state (Health, Gold, Inventory) from `semantic_tkg.py` (Neo4j).
    *   It also retrieves relevant past memories or world info.
4.  **Intent Detection (Key Feature)**:
    *   The `Orchestrator` asks Gemini: *"Given the user input and current state, which tool should I use?"*
    *   **Tools**: `attack`, `buy_item`, `sell_item` (defined in `dnd_tools`).
5.  **Execution**:
    *   **If Tool**: The specific Python function is executed (e.g., deducting gold and adding item to inventory in Neo4j).
    *   **If Narrative**: The Rule/Narrative agents determine the outcome based on game logic.
6.  **Response**:
    *   The `Orchestrator` bundles the **New Scene Description**, **Action Log** (combat results), and **Updated Player Stats**.
    *   Frontend updates the UI instantly.

---

## 🛠️ Development & Debugging

### useful Commands
*   **View Backend Logs**:
    ```bash
    docker-compose logs -f backend
    ```
*   **View Frontend Logs**:
    ```bash
    docker-compose logs -f frontend
    ```
*   **Rebuild Containers** (after changing `requirements.txt` or `package.json`):
    ```bash
    docker-compose up --build
    ```

### How to Add a New Feature
1.  **Backend**:
    *   Define the new capability in `semantic_tkg.py` (e.g., `cast_spell`).
    *   Add a tool definition for the LLM in `app/agents/tools.py` (if applicable).
    *   Handle the tool execution in `Orchestrator.process_turn`.
2.  **Frontend**:
    *   Update `StatsPanel` or create a new component if you are displaying new data.
    *   Ensure `PlayPage` fetches user stats correctly via `fetchRPGState`.
