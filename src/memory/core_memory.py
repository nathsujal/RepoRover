import json
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ValidationError

import logging
logger = logging.getLogger(__name__)

class Persona(BaseModel):
    """Defines the agent's persona."""
    name: str
    description: str
    instructions: List[str]


class UserPreferences(BaseModel):
    """Stores user-specific preferences."""
    programming_language: str = "python"


class CoreMemoryModel(BaseModel):
    """The root model for core memory data."""
    persona: Persona
    user_preferences: UserPreferences


class CoreMemory:
    """Manages the agent's core memory, handling loading and saving to a JSON file."""

    def __init__(self, file_path: Path):
        logger.info("Initializing Core Memory...")
        self.file_path = file_path
        self.data = self._load()

    def _load(self) -> CoreMemoryModel:
        """Loads core memory from the specified file, or creates a default if not found."""
        if self.file_path.exists():
            logger.info(f"Loading core memory from {self.file_path}")
            with open(self.file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    return CoreMemoryModel(**data)
                except (json.JSONDecodeError, ValidationError) as e:
                    print(f"Error loading core memory, creating default: {e}")
                    return self._create_default()
        else:
            logger.info("Core memory file not found, creating default.")
            return self._create_default()

    def _create_default(self) -> CoreMemoryModel:
        """Creates a default core memory configuration and saves it."""
        default_persona = Persona(
            name="RepoRover",
            description="An advanced AI agent that ingests and understands GitHub repositories using a sophisticated multi-agent and hybrid memory architecture, allowing for deep, context-aware conversations about any codebase.",
            instructions=[
                "Be helpful and informative.",
                "Provide context-aware answers about the codebase.",
                "Route tasks to specialized agents as needed."
            ]
        )
        default_prefs = UserPreferences()
        default_memory = CoreMemoryModel(persona=default_persona, user_preferences=default_prefs)
        self.save(default_memory)
        return default_memory

    def save(self, data: CoreMemoryModel):
        """Saves the provided core memory data to the file."""
        self.data = data
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data.dict(), f, indent=4)

    def get_persona(self) -> Persona:
        """Returns the current agent persona."""
        return self.data.persona

    def get_user_preferences(self) -> UserPreferences:
        """Returns the current user preferences."""
        return self.data.user_preferences


if __name__ == "__main__":
    core = CoreMemory(Path("data/memory/core_memory.json"))
    print(core.get_persona())