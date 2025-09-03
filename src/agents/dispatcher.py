"""
Dispatcher Agent: Manages the ingestion workflow for a repository.
"""
import logging
import json
from typing import Any, Dict, Type
from pathlib import Path
import os
import shutil
from pydantic import BaseModel

from .architect import ArchitectAgent
from .librarian import LibrarianAgent
from .annotator import AnnotatorAgent
from .information_retriever import InformationRetrieverAgent
from .synthesizer import SynthesizerAgent

from src.tools.repo_cloner import clone_repo, scan_repository

from src.memory.semantic_memory.manager import SemanticMemoryManager
from src.memory.core_memory import CoreMemory
from src.memory.episodic_memory.manager import EpisodicMemoryManager
from src.memory.procedural_memory.manager import ProceduralMemoryManager
from src.core.config import settings

logger = logging.getLogger(__name__)

class DispatcherConfig(BaseModel):
    """Configuration for the Dispatcher agent."""
    model_name: str = "N/A"
    model_class: Type = None
    agent_name: str = "dispatcher"
    description: str = "Routes requests and orchestrates the ingestion pipeline."

class DispatcherAgent():
    """
    The Dispatcher agent orchestrates the entire repository ingestion process.
    """

    def __init__(self, semantic_memory: SemanticMemoryManager):
        self.config = DispatcherConfig()
        self.name = self.config.agent_name
        self.description = self.config.description
        self.model = None

        # Clear the vector memory store
        vector_mem_dir = "data/memory/vector_memory"
        if os.path.exists(vector_mem_dir):
            shutil.rmtree(vector_mem_dir)
        # Clear the repo dir
        repo_dir = "data/repositories"
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        # The dispatcher holds the central memory and specialist agents
        self.semantic_memory = semantic_memory
        self.core_memory = CoreMemory(file_path=Path("data/memory/core_memory.json"))
        self.episodic_memory = EpisodicMemoryManager()
        self.procedural_memory = ProceduralMemoryManager(workflow_dir="workflows")

        self.agents: Dict[str, Any] = {
            "architect": ArchitectAgent(self.semantic_memory, self.core_memory, self.episodic_memory),
            "librarian": LibrarianAgent(self.semantic_memory, self.core_memory, self.episodic_memory),
            "annotator": AnnotatorAgent(self.semantic_memory, self.core_memory, self.episodic_memory),
            "information_retriever": InformationRetrieverAgent(self.semantic_memory),
            "synthesizer": SynthesizerAgent(),
        }

        logger.info(f"{self.name} agent initialized.")

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determines the workflow (ingestion or query) and executes it.

        Args:
            input_data: A dictionary containing either a 'github_url' for ingestion
                        or a 'question' for querying.
        """
        if "github_url" in input_data:
            self.episodic_memory.add_interaction(
                agent_name=self.name,
                interaction_type="user_request",
                content=f"Received request to ingest repository: {input_data['github_url']}"
            )
            return await self._handle_ingestion(input_data)
        elif "question" in input_data:
            self.episodic_memory.add_interaction(
                agent_name=self.name,
                interaction_type="user_request",
                content=f"Received query: {input_data['question']}"
            )
            return await self._handle_query(input_data)
        else:
            return {"status": "error", "message": "Invalid input. Must provide 'github_url' or 'question'."}

    async def _handle_ingestion(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handles the entire ingestion pipeline for a repository."""
        repo_url = input_data.get("github_url")
        logger.info(f"Starting ingestion process for {repo_url}")
        self.episodic_memory.add_interaction(
            agent_name=self.name,
            interaction_type="internal_thought",
            content=f"Starting ingestion pipeline for {repo_url}.",
            interaction_metadata={"repo_url": repo_url}
        )

        try:
            logger.info("Clearing all memory stores for a fresh ingestion...")
            await self.semantic_memory.clear_all()
            
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            local_repo_path = str(settings.REPOSITORIES_DIR / repo_name)

            # --- 1. Clone the Repository ---
            clone_repo(repo_url, local_repo_path)
            self.episodic_memory.add_interaction(
                agent_name=self.name,
                interaction_type="internal_action",
                content=f"Successfully cloned repository {repo_name} to {local_repo_path}.",
                interaction_metadata={"repo_name": repo_name, "path": local_repo_path}
            )

            # --- 2. Scan and Categorize Files ---
            categorized_files = scan_repository(local_repo_path)
            python_files = categorized_files.get("python", [])
            doc_files = categorized_files.get("markdown", [])
            
            logger.info(f"Scan complete: Found {len(python_files)} Python files and {len(doc_files)} docs.")
            self.episodic_memory.add_interaction(
                agent_name=self.name,
                interaction_type="internal_action",
                content=f"Scanned repository and found {len(python_files)} Python files and {len(doc_files)} documentation files.",
                interaction_metadata={"python_files_count": len(python_files), "doc_files_count": len(doc_files)}
            )

            # --- 3. Execute Ingestion Workflow ---
            initial_context = {
                "python_files": python_files,
                "doc_files": doc_files,
                "repo_name": repo_name
            }
            await self._execute_workflow("ingestion_workflow", initial_context)

            return {
                "status": "success",
                "message": f"Successfully ingested and analyzed {repo_url}."
            }

        except Exception as e:
            logger.exception(f"An error occurred during ingestion for {repo_url}")
            return {"status": "error", "message": str(e)}

    async def _execute_workflow(self, workflow_name: str, initial_context: Dict[str, Any]):
        """Executes a workflow from the procedural memory."""
        workflow = self.procedural_memory.get_workflow(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_name}' not found.")

        logger.info(f"Executing workflow: {workflow.name}")
        self.episodic_memory.add_interaction(
            agent_name=self.name,
            interaction_type="internal_action",
            content=f"Starting workflow '{workflow.name}'.",
            interaction_metadata={"workflow_name": workflow.name}
        )

        context = initial_context.copy()

        for step in workflow.steps:
            agent = self.agents.get(step.agent)
            if not agent:
                logger.error(f"Agent '{step.agent}' not found for step '{step.name}'.")
                continue

            # Prepare input for the agent by replacing placeholders
            step_input = {}
            if step.input:
                for key, value in step.input.items():
                    if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                        placeholder = value[2:-2]
                        
                        keys = placeholder.split('.')
                        resolved_value = context
                        try:
                            for k in keys:
                                resolved_value = resolved_value[k]
                            step_input[key] = resolved_value
                        except (KeyError, TypeError) as e:
                            logger.error(f"Could not resolve placeholder '{placeholder}': {e}")
                            step_input[key] = None
                    else:
                        step_input[key] = value

            if step.agent == "information_retriever":
                step_input['question'] = context.get('question')
                # Pass the planner's analysis for context, if available
                if 'planned_query' in context:
                    step_input['plan_analysis'] = context['planned_query'].get('analysis')
            
            logger.info(f"Executing step '{step.name}' with agent '{step.agent}'.")
            
            # Execute the agent and capture the output
            result = await agent.execute(step_input)

            # Update context with the result of the step
            if step.output:
                # Special handling for the retriever's output to pass to the synthesizer
                if step.agent == "information_retriever" and result.get("status") == "success":
                    context[step.output] = {
                        "collected_data": result.get("collected_data", [])
                    }
                else:
                    context[step.output] = result
            
            logger.info(f"\nContext: {context}\n")

        return context

    async def _handle_query(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handles the query pipeline by executing the query workflow."""
        logger.info("Query received. Routing to query pipeline...")
        try:

            recent_interactions = self.episodic_memory.get_recent_interactions(limit=5)
            conversation_history = "\n".join(
                [f"{inter.agent_name}: {inter.content}" for inter in recent_interactions]
            )
            persona = self.core_memory.get_persona()
            import json
            print(f"\n\nPERSONA: {persona}\n\n")

            initial_context = {
                "question": input_data.get("question"),
                "conversation_history": conversation_history,
                "persona": persona
            }
            # The result of the workflow execution will be the final context
            result = await self._execute_workflow("query_workflow", initial_context)
            return {"status": "success", "result": result}
        except Exception as e:
            logger.exception("An error occurred during the query process.")
            return {"status": "error", "message": str(e)}