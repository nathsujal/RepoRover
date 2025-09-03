import asyncio
import uuid
from fastapi import FastAPI, Request, BackgroundTasks
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

app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Global State ---
semantic_memory = SemanticMemoryManager()
dispatcher_agent = DispatcherAgent(semantic_memory)

# In-memory dictionary to track the status of ingestion tasks
ingestion_status = {}

# --- Pydantic Models for API ---
class IngestRequest(BaseModel):
    github_url: str

class QueryRequest(BaseModel):
    question: str

# --- Background Task Logic ---
async def run_ingestion(task_id: str, github_url: str):
    """
    A wrapper function to run the ingestion process in the background
    and update the task status.
    """
    logger.info(f"Starting background ingestion for task_id: {task_id}")
    ingestion_status[task_id] = {"status": "ingesting", "message": "Cloning repository and processing files..."}
    try:
        result = await dispatcher_agent.execute({"github_url": github_url})
        if result.get("status") == "success":
            ingestion_status[task_id] = {"status": "completed", "message": result.get("message")}
            logger.info(f"Ingestion task {task_id} completed successfully.")
        else:
            ingestion_status[task_id] = {"status": "error", "message": result.get("message", "An unknown error occurred.")}
            logger.error(f"Ingestion task {task_id} failed with message: {result.get('message')}")
    except Exception as e:
        logger.exception(f"A critical error occurred in ingestion task {task_id}")
        ingestion_status[task_id] = {"status": "error", "message": str(e)}


# --- API Endpoints ---
@app.post("/ingest")
async def ingest_repository(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to start ingesting a GitHub repository.
    This now returns a task_id for status polling.
    """
    logger.info(f"Received ingestion request for: {request.github_url}")
    task_id = str(uuid.uuid4())
    
    # Add the long-running ingestion task to the background
    background_tasks.add_task(run_ingestion, task_id, request.github_url)
    
    # Immediately respond with a task ID the client can use to check status
    return JSONResponse(
        content={"message": "Repository ingestion started.", "task_id": task_id},
        status_code=202  # Accepted
    )

@app.get("/ingest/status/{task_id}")
async def get_ingestion_status(task_id: str):
    """
    Endpoint for the client to poll for the status of an ingestion task.
    """
    status = ingestion_status.get(task_id)
    if not status:
        return JSONResponse(content={"status": "error", "message": "Task ID not found."}, status_code=404)
    return JSONResponse(content=status)

@app.post("/query")
async def query_repository(request: QueryRequest):
    """
    Endpoint to ask a question about the ingested repository.
    """
    logger.info(f"Received query: {request.question}")
    try:
        # This assumes ingestion is complete and the agent is ready.
        # In a production app, you might check the repo's ingestion status first.
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
@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("frontend/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return JSONResponse(
            content={"detail": "index.html not found. Make sure it's in the same directory as main.py."},
            status_code=404
        )

# --- Main Entry Point ---
if __name__ == "__main__":
    logger.info("Starting RepoRover server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)