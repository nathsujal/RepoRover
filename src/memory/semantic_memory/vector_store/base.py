"""Base vector store implementation."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

from pydantic import BaseModel

from src.core.exceptions import VectorStoreError
from src.memory.base import BaseMemory

T = TypeVar('T')

class VectorDocument(BaseModel):
    """A document with vector embeddings."""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}
    score: Optional[float] = None

class BaseVectorStore(BaseMemory[VectorDocument], ABC, Generic[T]):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    async def add_documents(
        self, 
        documents: List[VectorDocument],
        **kwargs: Any
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents to add
            **kwargs: Additional arguments
            
        Returns:
            List of document IDs
        """
        pass
    
    @abstractmethod
    async def similarity_search(
        self, 
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> List[VectorDocument]:
        """
        Search for similar documents.
        
        Args:
            query: The query string
            k: Number of results to return
            filter: Optional filter to apply
            **kwargs: Additional arguments
            
        Returns:
            List of matching documents with scores
        """
        pass
    
    @abstractmethod
    async def similarity_search_with_score(
        self, 
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> List[tuple[VectorDocument, float]]:
        """
        Search for similar documents with scores.
        
        Args:
            query: The query string
            k: Number of results to return
            filter: Optional filter to apply
            **kwargs: Additional arguments
            
        Returns:
            List of (document, score) tuples
        """
        pass
    
    @abstractmethod
    async def delete_by_ids(self, ids: List[str], **kwargs: Any) -> bool:
        """
        Delete documents by their IDs.
        
        Args:
            ids: List of document IDs to delete
            **kwargs: Additional arguments
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_by_metadata(
        self, 
        filter: Dict[str, Any],
        **kwargs: Any
    ) -> int:
        """
        Delete documents matching the filter.
        
        Args:
            filter: Filter to match documents
            **kwargs: Additional arguments
            
        Returns:
            Number of documents deleted
        """
        pass
