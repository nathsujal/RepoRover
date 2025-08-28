"""ChromaDB implementation of the vector store."""
import os
from typing import Any, Dict, List, Optional, cast

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from chromadb.api.types import (
    EmbeddingFunction,
    Documents,
    Embedding
)

import pandas as pd
from sklearn.manifold import TSNE
import plotly.express as px
import numpy as np

from ....core.exceptions import VectorStoreError
from .base import BaseVectorStore, VectorDocument
from .config import VectorStoreConfig
from src.memory.base import MemoryConfig

import logging
logger = logging.getLogger(__name__)

class SentenceTransformerEmbeddingFunction(EmbeddingFunction):
    """Embedding function using Sentence Transformers."""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """Initialize the embedding function."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except ImportError as e:
            raise ImportError(
                "Please install sentence-transformers: "
                "`pip install sentence-transformers`"
            ) from e
    
    def __call__(self, input: Documents) -> Embedding:
        """Generate embeddings for the input documents."""
        return cast(Embedding, self.model.encode(input, show_progress_bar=False).tolist())

class ChromaVectorStore(BaseVectorStore[VectorDocument]):
    """ChromaDB implementation of the vector store."""
    
    def __init__(self, config: VectorStoreConfig):
        """Initialize the ChromaDB vector store."""
        generic_config = MemoryConfig(
            memory_name="ChromaVectorStore",
            description="A persistent vector store using ChromaDB for semantic search."
        )
        super().__init__(generic_config)
        self.config = config
        self._client = self.create_client()
        self._embedding_function = self.generate_embedding_function()
        self._collection = self._get_or_create_collection()

    def _get_or_create_collection(self) -> chromadb.Collection:
        """Central method to initialize or re-initialize the collection."""
        self._collection = self._client.get_or_create_collection(
            name=self.config.collection_name,
            embedding_function=self._embedding_function
        )
        return self._collection
        
    def create_client(self) -> chromadb.ClientAPI:
        """Get the ChromaDB client."""
        logger.info("Created Chromadb client")
        self._client = chromadb.PersistentClient(
            path=self.config.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        return self._client
    
    def generate_embedding_function(self) -> EmbeddingFunction:
        """Get the embedding function."""
        self._embedding_function = SentenceTransformerEmbeddingFunction(
            model_name=self.config.embedding_model_name
        )
        return self._embedding_function
    
    async def store(
        self, 
        key: str, 
        value: VectorDocument, 
        **metadata: Dict[str, Any]
    ) -> bool:
        """Store a document in the vector store."""
        try:
            metadata = {**value.metadata, **metadata}
            self._collection.upsert(
                ids=[key],
                documents=[value.content],
                metadatas=[metadata],
            )
            return True
        except Exception as e:
            raise VectorStoreError(f"Failed to store document: {str(e)}")
    
    async def retrieve(self, key: str) -> Optional[VectorDocument]:
        """Retrieve a document by ID."""
        try:
            result = self._collection.get(ids=[key])
            if not result['ids']:
                return None
                
            return VectorDocument(
                id=result['ids'][0],
                content=result['documents'][0],
                metadata=result['metadatas'][0],
            )
        except Exception as e:
            raise VectorStoreError(f"Failed to retrieve document: {str(e)}")
    
    async def search(
        self, 
        query: str, 
        limit: int = 10, 
        **filters: Any
    ) -> List[Dict[str, Any]]:
        """Search for documents matching the query."""
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(limit, self.config.search_top_k),
                where=filters,
            )
            
            documents = []
            for i, doc_id in enumerate(results['ids'][0]):
                score = 1.0 - results['distances'][0][i]  # Convert distance to similarity
                if score < self.config.search_score_threshold:
                    continue
                    
                documents.append({
                    'id': doc_id,
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'score': score
                })
                
            return documents
        except Exception as e:
            raise VectorStoreError(f"Search failed: {str(e)}")
    
    async def delete(self, key: str) -> bool:
        """Delete a document by ID."""
        try:
            self._collection.delete(ids=[key])
            return True
        except Exception as e:
            raise VectorStoreError(f"Failed to delete document: {str(e)}")
    
    async def clear(self) -> bool:
        """Clear all documents from the vector store."""
        try:
            self._client.delete_collection(name=self.config.collection_name)
            self._get_or_create_collection()
            return True
        except Exception as e:
            if "does not exist" in str(e):
                self._get_or_create_collection()
                return True
            raise VectorStoreError(f"Failed to clear vector store: {str(e)}")
    
    async def add_documents(
        self, 
        documents: List[VectorDocument],
        **kwargs: Any
    ) -> List[str]:
        """Add multiple documents to the vector store."""
        try:
            ids = [doc.id for doc in documents]
            self._collection.upsert(
                ids=ids,
                documents=[f"{doc.id}: {doc.content}" for doc in documents],
                metadatas=[doc.metadata for doc in documents],
            )
            return ids
        except Exception as e:
            raise VectorStoreError(f"Failed to add documents: {str(e)}")
    
    async def similarity_search(
        self, 
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> List[VectorDocument]:
        """Search for similar documents."""
        results = await self.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter,
            **kwargs
        )
        return [doc for doc, _ in results]
    
    async def similarity_search_with_score(
        self, 
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> List[tuple[VectorDocument, float]]:
        """Search for similar documents with scores."""
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(k, self.config.search_top_k),
                where=filter,
                **kwargs
            )
            
            documents = []
            for i, doc_id in enumerate(results['ids'][0]):
                score = 1.0 - results['distances'][0][i]  # Convert distance to similarity
                if score < self.config.search_score_threshold:
                    continue
                    
                doc = VectorDocument(
                    id=doc_id,
                    content=results['documents'][0][i],
                    metadata=results['metadatas'][0][i],
                    score=score
                )
                documents.append((doc, score))
                
            return documents
        except Exception as e:
            raise VectorStoreError(f"Similarity search failed: {str(e)}")
    
    async def delete_by_ids(
        self, 
        ids: List[str], 
        **kwargs: Any
    ) -> bool:
        """Delete documents by their IDs."""
        try:
            self._collection.delete(ids=ids)
            return True
        except Exception as e:
            raise VectorStoreError(f"Failed to delete documents: {str(e)}")
    
    async def delete_by_metadata(
        self, 
        filter: Dict[str, Any],
        **kwargs: Any
    ) -> int:
        """Delete documents matching the filter."""
        try:
            # Get all matching document IDs
            results = self._collection.get(where=filter)
            if not results['ids']:
                return 0
                
            # Delete the matching documents
            await self.delete_by_ids(results['ids'])
            return len(results['ids'])
            
        except Exception as e:
            raise VectorStoreError(
                f"Failed to delete documents by metadata: {str(e)}"
            )

    def display(self):
        """
        Connects to a ChromaDB, performs t-SNE, and generates an interactive plot.
        """
        db_path = self.config.persist_directory
        collection_name = self.config.collection_name
        
        print("🚀 Starting ChromaDB visualization...")

        # 1. Connect to the ChromaDB client
        try:
            client = self._client
            print(f"✅ Connected to ChromaDB at path: {db_path}")
        except Exception as e:
            print(f"❌ Failed to connect to ChromaDB: {e}")
            return

        # 2. Get the collection
        try:
            collection = client.get_collection(name=collection_name)
            print(f"✅ Successfully retrieved collection: '{collection_name}'")
        except Exception as e:
            print(f"❌ Could not get collection '{collection_name}'. Error: {e}")
            print("   Make sure the collection exists and the path is correct.")
            return

        # 3. Fetch all data from the collection
        print("⏳ Fetching all data from the collection...")
        # The .get() method without IDs fetches all entries.
        # We include embeddings, metadatas, and documents.
        data = collection.get(include=["embeddings", "metadatas", "documents"])
        
        if not data or not data.get('ids'):
            print("❌ Collection is empty or data could not be retrieved.")
            return
            
        print(f"📊 Found {len(data['ids'])} documents in the collection.")

        # Ensure we have enough data points to visualize
        if len(data['ids']) < 2:
            print("❌ Need at least 2 documents in the collection to create a visualization.")
            return

        embeddings = np.array(data['embeddings'])
        documents = data['documents']
        metadatas = data['metadatas']
        
        # 4. Perform dimensionality reduction using t-SNE
        # t-SNE is great for visualizing high-dimensional data clusters.
        # n_components=2 means we are reducing to a 2D space.
        print("⏳ Performing t-SNE dimensionality reduction (this may take a moment)...")
        tsne = TSNE(n_components=2, perplexity=min(30, len(data['ids']) - 1), random_state=42)
        embeddings_2d = tsne.fit_transform(embeddings)
        print("✅ t-SNE complete.")

        # 5. Create a Pandas DataFrame for plotting
        # This makes it easy to manage the data for Plotly.
        df = pd.DataFrame({
            'x': embeddings_2d[:, 0],
            'y': embeddings_2d[:, 1],
            'document': documents,
            # Create a 'metadata_str' column for hover info, handling potential None values
            'metadata': [str(m) if m is not None else 'No Metadata' for m in metadatas]
        })

        # 6. Create an interactive plot with Plotly
        print("🎨 Creating interactive plot...")
        fig = px.scatter(
            df,
            x='x',
            y='y',
            hover_name='document',
            hover_data={'x': False, 'y': False, 'document': False, 'metadata': True},
            title=f"2D Visualization of Chroma Collection: '{collection_name}'",
            labels={'x': 't-SNE Component 1', 'y': 't-SNE Component 2'},
            template='plotly_white'
        )

        # Customize the hover template for better readability
        fig.update_traces(
            hovertemplate="<b>Document:</b> %{hovertext}<br><b>Metadata:</b> %{customdata[0]}<extra></extra>"
        )
        
        # Improve the layout
        fig.update_layout(
            title_font_size=20,
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False)
        )

        # 7. Save the plot to an HTML file
        output_file = "chroma_visualization.html"
        fig.write_html(output_file)
        print(f"🎉 Success! Interactive visualization saved to '{output_file}'")
        print("   Open this file in your web browser to explore the vector space.")
