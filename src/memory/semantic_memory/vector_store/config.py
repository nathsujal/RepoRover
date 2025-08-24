"""Configuration for VectorStore using ChromaDB."""
from typing import Optional, List, Dict, Any
from pydantic import Field

from src.core.config import Settings

class VectorStoreConfig(Settings):
    """Configuration for VectorStore."""
    
    # ChromaDB settings
    persist_directory: str = Field(
        default="./data/vector_store",
        description="Directory to persist the vector store"
    )
    collection_name: str = Field(
        default="documents",
        description="Name of the collection to store documents in"
    )
    
    # Embedding settings
    embedding_model_name: str = Field(
        default="BAAI/bge-small-en-v1.5",
        description="Hugging Face model name for embeddings"
    )
    embedding_dimension: int = Field(
        default=384,  # Default for bge-small
        description="Dimension of the embedding vectors"
    )
    
    # Indexing settings
    max_text_length: int = Field(
        default=8192,
        description="Maximum length of text to embed (in characters)"
    )
    batch_size: int = Field(
        default=32,
        description="Batch size for embedding generation"
    )
    
    # Search settings
    search_top_k: int = Field(
        default=5,
        description="Number of results to return for search queries"
    )
    search_score_threshold: float = Field(
        default=0.5,
        description="Minimum similarity score for search results (0.0 to 1.0)"
    )
    
    class Config:
        env_prefix = "VECTOR_STORE_"
        extra = "ignore"
