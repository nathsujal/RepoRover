import yaml
import os
from typing import Dict, Any

class CoreMemory:
    """
    Manages the core, static memory of the agent, including its persona
    and user-specific information, loaded from a YAML file.
    """
    def __init__(self, config_path: str = 'memory/config.yaml'):
        """
        Initializes the CoreMemory instance.

        Args:
            config_path (str): The path to the configuration YAML file.
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")
        
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Loads the YAML configuration file."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    @property
    def persona(self) -> Dict[str, Any]:
        """Returns the agent's persona information."""
        return self._config.get('persona', {})

    @property
    def user_profile(self) -> Dict[str, Any]:
        """Returns the user's profile information."""
        return self._config.get('user_profile', {})

    def reload(self):
        """Reloads the configuration from the file."""
        self._config = self._load_config()
        print("Core memory reloaded.")

# Example Usage:
if __name__ == '__main__':
    core_memory = CoreMemory()
    print("Agent Name:", core_memory.persona.get('name'))
    print("User's Preferred Language:", core_memory.user_profile.get('preferences', {}).get('primary_language'))