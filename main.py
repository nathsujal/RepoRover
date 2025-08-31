import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from src.agents.dispatcher import DispatcherAgent
from src.memory.semantic_memory.manager import SemanticMemoryManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastAPI App Initialization ---
app = FastAPI(
    title="RepoRover API",
    description="API for the RepoRover AI codebase companion.",
    version="0.1.0",
)

# --- Global State ---
# In a real application, you might manage this differently,
# but for a prototype, a global instance is straightforward.
semantic_memory = SemanticMemoryManager()
dispatcher_agent = DispatcherAgent(semantic_memory)

# --- Pydantic Models for API ---
class IngestRequest(BaseModel):
    github_url: str

class QueryRequest(BaseModel):
    question: str

# --- API Endpoints ---
@app.post("/ingest")
async def ingest_repository(request: IngestRequest):
    """
    Endpoint to ingest a GitHub repository.
    This is a long-running task.
    """
    logger.info(f"Received ingestion request for: {request.github_url}")
    try:
        # Running the dispatcher in the background to not block the server
        # In a production app, you'd use a task queue like Celery or RQ.
        asyncio.create_task(dispatcher_agent.execute({"github_url": request.github_url}))
        
        # Immediately respond to the client
        return JSONResponse(
            content={"message": "Repository ingestion started. This may take a few minutes."},
            status_code=202  # Accepted
        )
    except Exception as e:
        logger.exception("Failed to start ingestion process.")
        return JSONResponse(
            content={"detail": str(e)},
            status_code=500
        )

@app.post("/query")
async def query_repository(request: QueryRequest):
    """
    Endpoint to ask a question about the ingested repository.
    """
    logger.info(f"Received query: {request.question}")
    try:
        response = await dispatcher_agent.execute({"question": request.question})
        if response.get("status") == "error":
            return JSONResponse(content={"detail": response.get("message")}, status_code=500)
        return response
    except Exception as e:
        logger.exception("Failed to process query.")
        return JSONResponse(
            content={"detail": str(e)},
            status_code=500
        )

# --- Serving the Frontend ---
# This serves your single index.html file.
@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return JSONResponse(
            content={"detail": "index.html not found. Make sure it's in the same directory as main.py."},
            status_code=404
        )

# --- Main Entry Point ---
if __name__ == "__main__":
    logger.info("Starting RepoRover server...")
    # Make sure to place main.py and index.html in the root of your project directory.
    uvicorn.run(app, host="0.0.0.0", port=8000)


