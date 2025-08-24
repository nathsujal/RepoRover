"""
Base memory class that defines the common interface for all memory systems.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

from pydantic import BaseModel, ConfigDict

T = TypeVar('T')

class MemoryConfig(BaseModel):
    """Base configuration for memory systems."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    memory_name: str
    description: str
    persistent: bool = True
    
class BaseMemory(ABC, Generic[T]):
    """Abstract base class for all memory systems."""
    
    def __init__(self, config: MemoryConfig):
        """Initialize the memory with the given configuration."""
        self.config = config
        self.name = config.memory_name
        self.description = config.description
        self.persistent = config.persistent
    
    @abstractmethod
    async def store(self, key: str, value: T, **metadata: Dict[str, Any]) -> bool:
        """Store a value with the given key and metadata."""
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> Optional[T]:
        """Retrieve a value by key."""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10, **filters: Any) -> List[Dict[str, Any]]:
        """Search for values matching the query and filters."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value by key."""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all values from the memory."""
        pass
    
    async def __setitem__(self, key: str, value: T) -> None:
        """Support for dict-like assignment."""
        await self.store(key, value)
    
    async def __getitem__(self, key: str) -> T:
        """Support for dict-like access."""
        result = await self.retrieve(key)
        if result is None:
            raise KeyError(f"Key not found: {key}")
        return result
