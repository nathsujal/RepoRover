import chromadb
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import hashlib

class VectorStore:
    """
    Manages vector storage for semantic search and document retrieval.
    Uses ChromaDB for efficient similarity search.
    """
    
    def __init__(self, persist_directory: str = "data/vector_store", collection_name: str = "documents"):
        """
        Initialize the vector store.
        
        Args:
            persist_directory (str): Directory to persist the vector database
            collection_name (str): Name of the collection to use
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Use a simple embedding function to avoid download timeouts
        try:
            # Try to use a simple embedding function first
            embedding_function = embedding_functions.DefaultEmbeddingFunction()
        except Exception:
            # Fallback to a basic function if embedding fails
            embedding_function = None
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function,
            metadata={"description": "Document storage for semantic search"}
        )
    
    def add_documents(self, documents: List[Dict[str, Any]], 
                     metadatas: Optional[List[Dict[str, Any]]] = None,
                     ids: Optional[List[str]] = None) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents (List[Dict[str, Any]]): List of documents with 'text' and 'metadata' keys
            metadatas (Optional[List[Dict[str, Any]]]): Additional metadata for each document
            ids (Optional[List[str]]): Custom IDs for documents
            
        Returns:
            List[str]: List of document IDs
        """
        if not documents:
            return []
        
        # Prepare data
        texts = []
        doc_metadatas = []
        doc_ids = []
        
        for i, doc in enumerate(documents):
            # Extract text content
            if isinstance(doc, dict):
                text = doc.get('text', str(doc))
                metadata = doc.get('metadata', {})
            else:
                text = str(doc)
                metadata = {}
            
            # Add additional metadata if provided
            if metadatas and i < len(metadatas):
                metadata.update(metadatas[i])
            
            # Generate ID if not provided
            if ids and i < len(ids):
                doc_id = ids[i]
            else:
                doc_id = self._generate_document_id(text, metadata)
            
            texts.append(text)
            doc_metadatas.append(metadata)
            doc_ids.append(doc_id)
        
        # Add to collection
        self.collection.add(
            documents=texts,
            metadatas=doc_metadatas,
            ids=doc_ids
        )
        
        return doc_ids
    
    def search(self, query: str, n_results: int = 10, 
               filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query (str): Search query
            n_results (int): Number of results to return
            filter_metadata (Optional[Dict[str, Any]]): Metadata filters
            
        Returns:
            List[Dict[str, Any]]: List of search results with documents, metadata, and distances
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_metadata
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                result = {
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'id': results['ids'][0][i],
                    'distance': results['distances'][0][i] if results['distances'] else None
                }
                formatted_results.append(result)
        
        return formatted_results
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by ID.
        
        Args:
            document_id (str): ID of the document to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Document data or None if not found
        """
        results = self.collection.get(ids=[document_id])
        
        if results['documents'] and results['documents'][0]:
            return {
                'document': results['documents'][0],
                'metadata': results['metadatas'][0],
                'id': results['ids'][0]
            }
        
        return None
    
    def update_document(self, document_id: str, new_text: str, 
                       new_metadata: Optional[Dict[str, Any]] = None):
        """
        Update an existing document.
        
        Args:
            document_id (str): ID of the document to update
            new_text (str): New text content
            new_metadata (Optional[Dict[str, Any]]): New metadata
        """
        # Get existing metadata if not provided
        if new_metadata is None:
            existing = self.get_document(document_id)
            if existing:
                new_metadata = existing['metadata']
            else:
                new_metadata = {}
        
        # Update the document
        self.collection.update(
            ids=[document_id],
            documents=[new_text],
            metadatas=[new_metadata]
        )
    
    def delete_document(self, document_id: str):
        """
        Delete a document from the vector store.
        
        Args:
            document_id (str): ID of the document to delete
        """
        self.collection.delete(ids=[document_id])
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.
        
        Returns:
            Dict[str, Any]: Collection statistics
        """
        count = self.collection.count()
        
        # Get a sample of documents to analyze metadata
        sample_results = self.collection.get(limit=100)
        metadata_keys = set()
        
        if sample_results['metadatas']:
            for metadata in sample_results['metadatas']:
                if metadata:
                    metadata_keys.update(metadata.keys())
        
        return {
            'total_documents': count,
            'collection_name': self.collection_name,
            'metadata_keys': list(metadata_keys),
            'persist_directory': self.persist_directory
        }
    
    def search_by_metadata(self, metadata_filter: Dict[str, Any], 
                          n_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search for documents by metadata filters.
        
        Args:
            metadata_filter (Dict[str, Any]): Metadata filters to apply
            n_results (int): Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of matching documents
        """
        results = self.collection.get(
            where=metadata_filter,
            limit=n_results
        )
        
        formatted_results = []
        if results['documents']:
            for i in range(len(results['documents'])):
                result = {
                    'document': results['documents'][i],
                    'metadata': results['metadatas'][i],
                    'id': results['ids'][i]
                }
                formatted_results.append(result)
        
        return formatted_results
    
    def _generate_document_id(self, text: str, metadata: Dict[str, Any]) -> str:
        """
        Generate a unique document ID based on content and metadata.
        
        Args:
            text (str): Document text
            metadata (Dict[str, Any]): Document metadata
            
        Returns:
            str: Unique document ID
        """
        content_hash = hashlib.md5(
            (text + json.dumps(metadata, sort_keys=True)).encode()
        ).hexdigest()
        
        return f"doc_{content_hash[:12]}"
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        self.collection.delete(where={})
    
    def backup_collection(self, backup_path: str):
        """
        Create a backup of the collection.
        
        Args:
            backup_path (str): Path to save the backup
        """
        # Get all documents
        results = self.collection.get()
        
        backup_data = {
            'collection_name': self.collection_name,
            'documents': results['documents'],
            'metadatas': results['metadatas'],
            'ids': results['ids']
        }
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
    
    def restore_collection(self, backup_path: str):
        """
        Restore collection from backup.
        
        Args:
            backup_path (str): Path to the backup file
        """
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        # Clear existing collection
        self.clear_collection()
        
        # Restore documents
        if backup_data['documents']:
            self.collection.add(
                documents=backup_data['documents'],
                metadatas=backup_data['metadatas'],
                ids=backup_data['ids']
            )

# Example usage
if __name__ == "__main__":
    vector_store = VectorStore()
    
    # Add some example documents
    documents = [
        {
            'text': 'Python is a programming language known for its simplicity.',
            'metadata': {'type': 'programming', 'language': 'python'}
        },
        {
            'text': 'Machine learning is a subset of artificial intelligence.',
            'metadata': {'type': 'ai', 'topic': 'machine_learning'}
        }
    ]
    
    doc_ids = vector_store.add_documents(documents)
    print(f"Added {len(doc_ids)} documents")
    
    # Search for documents
    results = vector_store.search("programming language", n_results=5)
    print(f"Found {len(results)} results")
    
    # Get collection stats
    stats = vector_store.get_collection_stats()
    print(f"Collection stats: {stats}")
