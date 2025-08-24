"""
Dispatcher Agent: Manages the ingestion workflow for a repository.
"""
import logging
from typing import Any, Dict, Type, List

from .base import AgentConfig, BaseAgent
from .architect import ArchitectAgent
from .librarian import LibrarianAgent
from .annotator import AnnotatorAgent

from src.tools.repo_cloner import clone_repo, scan_repository

from src.memory.semantic_memory.manager import SemanticMemoryManager
from src.core.config import settings

logger = logging.getLogger(__name__)

class DispatcherConfig(AgentConfig):
    """Configuration for the Dispatcher agent."""
    model_name: str = "N/A"
    model_class: Type = None

class DispatcherAgent(BaseAgent):
    """
    The Dispatcher agent orchestrates the entire repository ingestion process.
    """

    def __init__(self, semantic_memory: SemanticMemoryManager):
        config = DispatcherConfig(
            agent_name="dispatcher",
            description="Routes requests and orchestrates the ingestion pipeline."
        )
        # We manually initialize to avoid loading an LLM for the dispatcher itself
        self.config = config
        self.name = config.agent_name
        self.description = config.description
        self.model = None

        # The dispatcher holds the central memory and specialist agents
        self.semantic_memory = semantic_memory
        self.architect = ArchitectAgent(self.semantic_memory)
        self.librarian = LibrarianAgent(self.semantic_memory)
        self.annotator = AnnotatorAgent(self.semantic_memory)
        # self.query_planner = QueryPlannerAgent(self.semantic_memory)

        logger.info(f"{self.name} agent initialized.")

    @classmethod
    def get_config_class(cls) -> Type[AgentConfig]:
        """Get the configuration class for this agent."""
        return DispatcherConfig

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determines the workflow (ingestion or query) and executes it.

        Args:
            input_data: A dictionary containing either a 'github_url' for ingestion
                        or a 'question' for querying.
        """
        if "github_url" in input_data:
            return await self._handle_ingestion(input_data)
        elif "question" in input_data:
            # This will be implemented in the query phase
            return await self._handle_query(input_data)
        else:
            return {"status": "error", "message": "Invalid input. Must provide 'github_url' or 'question'."}

    async def _handle_ingestion(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handles the entire ingestion pipeline for a repository."""
        repo_url = input_data.get("github_url")
        logger.info(f"Starting ingestion process for {repo_url}")

        try:
            logger.info("Clearing all memory stores for a fresh ingestion...")
            await self.semantic_memory.clear_all()
            
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            local_repo_path = str(settings.REPOSITORIES_DIR / repo_name)

            # --- 1. Clone the Repository ---
            clone_repo(repo_url, local_repo_path)

            # --- 2. Scan and Categorize Files ---
            categorized_files = scan_repository(local_repo_path)
            python_files = categorized_files.get("python", [])
            doc_files = categorized_files.get("markdown", [])
            
            logger.info(f"Scan complete: Found {len(python_files)} Python files and {len(doc_files)} docs.")

            # --- 3. Orchestrate Specialist Agents ---
            if python_files:
                await self.architect.execute({"file_paths": python_files})
            
            if doc_files:
                await self.librarian.execute({"doc_file_paths": doc_files})

            logger.info("Dispatcher: Handing off to Annotator Agent for code summarization...")
            
            # --- 4. Annotate Code Entities ---
            await self.annotator.execute({})

            return {
                "status": "success",
                "message": f"Successfully ingested and analyzed {repo_url}."
            }

        except Exception as e:
            logger.exception(f"An error occurred during ingestion for {repo_url}")
            return {"status": "error", "message": str(e)}

    async def _handle_query(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """(Placeholder) Handles the query pipeline."""
        logger.info("Query received. Routing to query pipeline...")
        # In the future, this will call the Query Planner agent.
        return {"status": "pending", "message": "Query handling not yet implemented."}