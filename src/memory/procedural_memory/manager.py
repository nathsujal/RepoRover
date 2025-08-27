"""
Procedural Memory Manager: Loads and executes predefined workflows from JSON files.
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any, List

from .workflow import Workflow

import logging
logger = logging.getLogger(__name__)

class ProceduralMemoryManager:
    """
    Manages the loading and execution of procedural workflows.
    """
    def __init__(self, workflow_dir: str):
        logger.info("Initializing Procedural Memory Manager...")
        self.workflow_dir = Path(workflow_dir)
        self.workflows: Dict[str, Workflow] = self._load_workflows()

    def _load_workflows(self) -> Dict[str, Workflow]:
        """Loads all workflow JSON files from the specified directory."""
        logger.info("Loading workflows...")
        workflows = {}
        if not self.workflow_dir.exists():
            logger.warning(f"Workflow directory not found: {self.workflow_dir}")
            return {}

        for file_path in self.workflow_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    workflow = Workflow(**data)
                    if workflow.name in workflows:
                        logger.warning(f"Duplicate workflow name '{workflow.name}' found. Overwriting.")
                    workflows[workflow.name] = workflow
                    logger.info(f"Successfully loaded workflow: {workflow.name}")
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from {file_path}")
            except Exception as e:
                logger.error(f"Failed to load workflow from {file_path}: {e}")
        return workflows

    def get_workflow(self, name: str) -> Workflow:
        """Retrieves a loaded workflow by name."""
        workflow = self.workflows.get(name)
        if not workflow:
            raise ValueError(f"Workflow '{name}' not found.")
        return workflow

    def list_workflows(self) -> List[str]:
        """Lists the names of all loaded workflows."""
        return list(self.workflows.keys())
