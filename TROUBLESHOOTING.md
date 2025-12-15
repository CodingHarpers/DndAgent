# 🐛 Troubleshooting Guide

This guide covers common issues you might encounter when specific setup or running the A.R.C.A.N.A. project.

## 🔑 API Key Issues

### "Google API Key not found" or Generation Failures
*   **Symptom**: The application crashes on startup, or the narrative agent returns empty/error responses.
*   **Cause**: The `GOOGLE_API_KEY` is missing or incorrect in the `.env` file.
*   **Solution**:
    1.  Check your `.env` file in the `DndAgent` root directory.
    2.  Ensure it contains `GOOGLE_API_KEY=your_key_here` (no quotes).
    3.  Restart the backend container: `docker-compose restart backend`.

## 🗄️ Database & Docker Issues

### "Connection Refused" to Neo4j
*   **Symptom**: The backend logs show errors connecting to `bolt://neo4j:7687`.
*   **Cause**: The Neo4j container is not running or hasn't finished starting up.
*   **Solution**:
    1.  Check container status: `docker-compose ps`.
    2.  If the container is not running, check logs: `docker-compose logs neo4j`.
    3.  Wait a few seconds and try again; Neo4j takes a moment to initialize.

### "Database Empty" / Characters Not Found
*   **Symptom**: You start a game but the world is empty, or you cannot buy items.
*   **Cause**: The seeding script hasn't been run.
*   **Solution**:
    Run the seed command:
    ```bash
    docker-compose exec backend python -m app.scripts.seed
    ```

## 🛠️ General Debugging

### Viewing Logs
To see what's happening under the hood:
*   **Backend Logs**: `docker-compose logs -f backend`
*   **Frontend Logs**: `docker-compose logs -f frontend`

### Rebuilding
If you changed `requirements.txt` (Backend) or `package.json` (Frontend), you need to rebuild the containers:
```bash
docker-compose up --build
```
