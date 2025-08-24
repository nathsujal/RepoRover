"""Base model interface for all language models."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

class ModelConfig(BaseModel):
    """Base configuration for models."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")
    
    model_name: str = Field(
        ...,
        description="Hugging Face model ID or path to load the model from"
    )
    device: str = Field(
        default="auto",
        description="Device to run the model on (auto, cuda, cpu, cuda:0, etc.)"
    )
    load_in_4bit: bool = Field(
        default=True,
        description="Whether to load the model in 4-bit precision"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for text generation"
    )
    max_new_tokens: int = Field(
        default=512,
        gt=0,
        description="Maximum number of new tokens to generate"
    )

class BaseModel(ABC):
    """Abstract base class for all language models."""
    
    def __init__(self, config: ModelConfig):
        """Initialize the model with the given configuration."""
        self.config = config
        self.model = None
        self.tokenizer = None
        self._load_model()
        
    @abstractmethod
    def _load_model(self) -> None:
        """Load the model and tokenizer."""
        pass
        
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text from the model.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            The generated text
        """
        pass
        
    @abstractmethod
    async def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for the input text(s).
        
        Args:
            text: Input text or list of texts
            
        Returns:
            List of embeddings, one for each input text
        """
        pass
    
    def to(self, device: str) -> None:
        """Move the model to the specified device."""
        if self.model is not None:
            self.model.to(device)
    
    def __str__(self) -> str:
        """String representation of the model."""
        return f"{self.__class__.__name__}(model_name='{self.config.model_name}')"
