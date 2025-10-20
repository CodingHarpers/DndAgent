# A.R.C.A.N.A. Project Instructions

## Overview
This document outlines how to setup, run, and test the A.R.C.A.N.A. (Agentic Rules-based & Creative Autonomous Narrative Architecture) codebase.

## Prerequisites
- Python 3.10 or higher
- [Poetry](https://python-poetry.org/) (Dependency Management)

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <repository_url>
    cd ARCANA
    ```

2.  **Install dependencies**:
    ```bash
    poetry install
    ```
    *Note: If you do not have poetry installed, you can manually install the required packages listed in `pyproject.toml`.*

## Running the Application

The main entry point is `src/main.py`. This script demonstrates the core "Merge Logic" which integrates the Memory, RuleRAG, and Storytelling modules.

To run the simulation:

```bash
# Make sure you are in the root directory
python -m src.main
```

### Expected Output
You should see an output indicating the flow of the turn:
1.  **Processing Player Action:** The system receives the input.
2.  **Memory Context Retrieved:** Simulating data fetch from Vector/Graph DBs.
3.  **Rule Adjudication:** The Rules Lawyer checks the action against logic.
4.  **Final Merged Output:** A JSON object combining the narrative description and the game state updates.

## Testing

Currently, the project is in the structure phase. You can add tests in the `tests/` directory.

To run tests (once added):
```bash
poetry run pytest
```

## Module Details

-   **`src/main.py`**: Contains the `ArcanaSystem` class and the `game_loop`. This is where the `_merge_outputs` function resides, combining narrative "Fluff" with game mechanic "Crunch".
-   **`src/storytelling/`**: Handles narrative generation (Narrator).
-   **`src/memory/`**: Manages state (Episodic & Semantic memory).
-   **`src/rulerag/`**: Handles game logic enforcement (Rules Lawyer).

## Next Steps for Development
1.  Implement actual database connections in `src/memory/router.py`.
2.  Connect to LLM providers (OpenAI, Anthropic, etc.) in `src/storytelling/orchestrator.py`.
3.  Populate `data/rules/` with actual JSON rule files.
