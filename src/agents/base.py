"""
Base agent class that defines the common interface for all agents.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from ..models.base import BaseModel as BaseLLMModel, ModelConfig

T = TypeVar('T', bound='BaseAgent')

class AgentConfig(BaseModel):
    """Base configuration for agents."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
    
    agent_name: str = Field(..., description="Unique name for the agent")
    description: str = Field(..., description="Description of the agent's purpose")
    
    # Model configuration
    model_name: str = Field(
        default="mistralai/Mistral-7B-v0.1",
        description="Hugging Face model ID or path to load"
    )
    model_class: Optional[Type[BaseLLMModel]] = Field(
        default=None,
        description="The model class to use for this agent"
    )
    
    # Generation parameters
    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Controls randomness in generation (lower = more deterministic)"
    )
    max_new_tokens: int = Field(
        default=1024,
        gt=0,
        description="Maximum number of new tokens to generate"
    )
    
    # Memory settings
    use_memory: bool = Field(
        default=True,
        description="Whether to use memory for this agent"
    )
    
    # Hardware settings
    device: str = Field(
        default="auto",
        description="Device to run the model on (auto, cuda, cpu, cuda:0, etc.)"
    )
    load_in_4bit: bool = Field(
        default=True,
        description="Whether to load the model in 4-bit precision"
    )

class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the agent with the given configuration."""
        self.config = config
        self.name = config.agent_name
        self.description = config.description
        self.model: Optional[BaseModel] = None

        # Only set up a model if a model_class is provided
        if self.config.model_class:
            self._setup_model()
        
    def _setup_model(self) -> None:
        """Set up the language model based on configuration."""
        try:
            model_config = ModelConfig(
                model_name=self.config.model_name,
                device=self.config.device,
                load_in_4bit=self.config.load_in_4bit,
                temperature=self.config.temperature,
                max_new_tokens=self.config.max_new_tokens
            )
            self.model = self.config.model_class(model_config)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load model {self.config.model_name} for agent {self.name}: {str(e)}"
            )
    
    @classmethod
    def from_config(cls: Type[T], config_dict: Dict[str, Any]) -> T:
        """Create an agent instance from a configuration dictionary."""
        config = cls.get_config_class()(**config_dict)
        return cls(config)
    
    @classmethod
    @abstractmethod
    def get_config_class(cls) -> Type[AgentConfig]:
        """Get the configuration class for this agent."""
        return AgentConfig
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main functionality.
        
        Args:
            input_data: Input data for the agent to process
            
        Returns:
            Dictionary containing the agent's output
        """
        pass
    
    async def __call__(self, *args, **kwargs) -> Dict[str, Any]:
        """Make the agent callable."""
        return await self.execute(*args, **kwargs)
    
    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(name='{self.name}')"
