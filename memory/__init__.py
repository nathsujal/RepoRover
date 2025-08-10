"""
Memory system for the RepoRover agent.

This module provides a comprehensive memory system with multiple components:
- CoreMemory: Static configuration and persona
- EpisodicMemory: Conversation history and experiences
- VectorStore: Semantic search and document retrieval
- GraphDatabase: Knowledge graph and relationships
- ResourceMemory: File and resource tracking
- MemoryManager: Unified interface for all memory components
"""

from dataclasses import asdict
import datetime
from .core_memory import CoreMemory
from .episodic_memory import EpisodicMemory, MemoryEntry
from .vector_store import VectorStore
from .graph_db import Neo4jGraphDatabase as GraphDatabase, Node, Relationship
from .resource_memory import ResourceMemory, Resource

__all__ = [
    'CoreMemory',
    'EpisodicMemory', 
    'MemoryEntry',
    'VectorStore',
    'GraphDatabase',
    'Node',
    'Relationship',
    'ResourceMemory',
    'Resource',
    'MemoryManager'
]

class MemoryManager:
    """
    Unified memory manager that coordinates all memory components.
    Provides a high-level interface for memory operations.
    """
    
    def __init__(self, config_path: str = "memory/config.yaml"):
        """
        Initialize the memory manager with all components.
        
        Args:
            config_path (str): Path to the configuration file
        """
        # Initialize all memory components
        self.core_memory = CoreMemory(config_path)
        self.episodic_memory = EpisodicMemory()
        self.vector_store = VectorStore()
        self.graph_db = GraphDatabase()
        self.resource_memory = ResourceMemory()
        
        # Track memory usage and performance
        self._access_count = 0
        self._last_cleanup = None
    
    def store_conversation(self, agent_name: str, user_message: str, 
                          agent_response: str, metadata: dict = None) -> str:
        """
        Store a conversation exchange in episodic memory.
        
        Args:
            agent_name (str): Name of the agent that responded
            user_message (str): User's message
            agent_response (str): Agent's response
            metadata (dict): Additional metadata
            
        Returns:
            str: Memory ID
        """
        content = {
            "user_message": user_message,
            "agent_response": agent_response,
            "timestamp": str(datetime.datetime.now())
        }
        
        return self.episodic_memory.store_memory(
            agent_name=agent_name,
            event_type="conversation",
            content=content,
            metadata=metadata or {},
            importance=0.7
        )
    
    def store_document(self, text: str, metadata: dict = None, 
                      document_id: str = None) -> str:
        """
        Store a document in the vector store.
        
        Args:
            text (str): Document text
            metadata (dict): Document metadata
            document_id (str): Custom document ID
            
        Returns:
            str: Document ID or None if vector store not available
        """
        if not self.vector_store:
            print("Warning: Cannot store document - VectorStore not available")
            return None
        
        documents = [{"text": text, "metadata": metadata or {}}]
        doc_ids = self.vector_store.add_documents(documents, ids=[document_id] if document_id else None)
        return doc_ids[0] if doc_ids else None
    
    def search_documents(self, query: str, n_results: int = 10) -> list:
        """
        Search for documents using semantic search.
        
        Args:
            query (str): Search query
            n_results (int): Number of results to return
            
        Returns:
            list: Search results
        """
        if not self.vector_store:
            print("Warning: Cannot search documents - VectorStore not available")
            return []
        
        return self.vector_store.search(query, n_results=n_results)
    
    def create_knowledge_node(self, labels: list, properties: dict, 
                            node_id: str = None) -> str:
        """
        Create a node in the knowledge graph.
        
        Args:
            labels (list): Node labels
            properties (dict): Node properties
            node_id (str): Custom node ID
            
        Returns:
            str: Node ID
        """
        if not self.graph_db:
            print("Warning: Cannot create knowledge node - GraphDatabase not available")
            return None
        
        return self.graph_db.create_node(labels, properties, node_id)
    
    def create_relationship(self, start_node_id: str, end_node_id: str,
                          relationship_type: str, properties: dict = None) -> str:
        """
        Create a relationship between nodes.
        
        Args:
            start_node_id (str): Start node ID
            end_node_id (str): End node ID
            relationship_type (str): Type of relationship
            properties (dict): Relationship properties
            
        Returns:
            str: Relationship ID
        """
        if not self.graph_db:
            print("Warning: Cannot create relationship - GraphDatabase not available")
            return None
        
        return self.graph_db.create_relationship(
            start_node_id, end_node_id, relationship_type, properties
        )
    
    def add_resource(self, path: str, resource_type: str, 
                    metadata: dict = None) -> str:
        """
        Add a resource to resource memory.
        
        Args:
            path (str): Resource path
            resource_type (str): Type of resource
            metadata (dict): Resource metadata
            
        Returns:
            str: Resource ID
        """
        return self.resource_memory.add_resource(path, resource_type, metadata)
    
    def get_conversation_history(self, limit: int = 20) -> list:
        """
        Get recent conversation history.
        
        Args:
            limit (int): Number of conversations to retrieve
            
        Returns:
            list: Conversation history
        """
        return self.episodic_memory.get_conversation_history(limit)
    
    def get_agent_config(self, agent_name: str) -> dict:
        """
        Get configuration for a specific agent.
        
        Args:
            agent_name (str): Name of the agent
            
        Returns:
            dict: Agent configuration
        """
        agents = self.core_memory._config.get('agents', [])
        for agent in agents:
            if agent.get('name') == agent_name:
                return agent
        return {}
    
    def search_memories(self, query: str, limit: int = 20) -> list:
        """
        Search across all memory types.
        
        Args:
            query (str): Search query
            limit (int): Number of results to return
            
        Returns:
            list: Combined search results
        """
        results = {
            'episodic': self.episodic_memory.search_memories(query, limit),
            'resources': self.resource_memory.search_resources(query, limit)
        }
        
        # Add optional components if available
        if self.vector_store:
            results['documents'] = self.vector_store.search(query, limit)
        else:
            results['documents'] = []
        
        if self.graph_db:
            results['knowledge'] = self.graph_db.search_nodes(properties={'name': query}, limit=limit)
        else:
            results['knowledge'] = []
        
        return results
    
    def get_memory_stats(self) -> dict:
        """
        Get comprehensive statistics about all memory components.
        
        Returns:
            dict: Memory statistics
        """
        stats = {
            'core_memory': {
                'agents': len(self.core_memory._config.get('agents', [])),
                'config_loaded': True
            },
            'episodic_memory': self.episodic_memory.get_memory_stats(),
            'resource_memory': self.resource_memory.get_resource_stats(),
            'total_access_count': self._access_count
        }
        
        # Add optional components if available
        if self.vector_store:
            stats['vector_store'] = self.vector_store.get_collection_stats()
        else:
            stats['vector_store'] = {'status': 'not_available'}
        
        if self.graph_db:
            stats['graph_database'] = self.graph_db.get_graph_stats()
        else:
            stats['graph_database'] = {'status': 'not_available'}
        
        return stats
    
    def cleanup_old_memories(self, days_old: int = 30) -> dict:
        """
        Clean up old memories and invalid resources.
        
        Args:
            days_old (int): Age threshold for cleanup
            
        Returns:
            dict: Cleanup statistics
        """
        cleanup_stats = {
            'episodic_cleaned': 0,
            'resources_cleaned': 0,
            'documents_cleaned': 0
        }
        
        # Clean up old episodic memories
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_old)
        old_memories = self.episodic_memory.retrieve_memories(
            limit=1000,
            min_importance=0.0
        )
        
        for memory in old_memories:
            if memory.timestamp < cutoff_date and memory.importance < 0.5:
                self.episodic_memory.delete_memory(memory.id)
                cleanup_stats['episodic_cleaned'] += 1
        
        # Clean up invalid resources
        cleanup_stats['resources_cleaned'] = self.resource_memory.cleanup_invalid_resources()
        
        self._last_cleanup = datetime.datetime.now()
        return cleanup_stats
    
    def backup_memory(self, backup_dir: str = "data/backups"):
        """
        Create backups of all memory components.
        
        Args:
            backup_dir (str): Directory to store backups
        """
        import os
        import shutil
        from datetime import datetime
        
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Backup episodic memory
        episodic_backup = os.path.join(backup_dir, f"episodic_{timestamp}.db")
        shutil.copy2(self.episodic_memory.db_path, episodic_backup)
        
        # Backup resource memory
        resource_backup = os.path.join(backup_dir, f"resource_{timestamp}.db")
        shutil.copy2(self.resource_memory.db_path, resource_backup)
        
        # Backup vector store (if available)
        vector_backup = None
        if self.vector_store:
            vector_backup = os.path.join(backup_dir, f"vector_{timestamp}")
            self.vector_store.backup_collection(vector_backup)
        
        # Backup config
        config_backup = os.path.join(backup_dir, f"config_{timestamp}.yaml")
        shutil.copy2(self.core_memory.config_path, config_backup)
        
        return {
            'episodic_backup': episodic_backup,
            'resource_backup': resource_backup,
            'vector_backup': vector_backup,
            'config_backup': config_backup
        }
    
    def get_agent_context(self, agent_name: str, context_size: int = 5) -> dict:
        """
        Get context for a specific agent including recent memories and related information.
        
        Args:
            agent_name (str): Name of the agent
            context_size (int): Number of recent memories to include
            
        Returns:
            dict: Agent context
        """
        # Get agent configuration
        agent_config = self.get_agent_config(agent_name)
        
        # Get recent memories for this agent
        recent_memories = self.episodic_memory.retrieve_memories(
            agent_name=agent_name,
            limit=context_size
        )
        
        # Get recent conversations
        recent_conversations = self.get_conversation_history(context_size)
        
        # Get popular resources
        popular_resources = self.resource_memory.get_popular_resources(10)
        
        return {
            'agent_config': agent_config,
            'recent_memories': [asdict(memory) for memory in recent_memories],
            'recent_conversations': recent_conversations,
            'popular_resources': [asdict(resource) for resource in popular_resources],
            'memory_stats': self.get_memory_stats()
        }
    
    def close(self):
        """Close all memory connections."""
        if self.graph_db and hasattr(self.graph_db, 'close'):
            self.graph_db.close()

# Convenience function to create a memory manager instance
def create_memory_manager(config_path: str = "memory/config.yaml") -> MemoryManager:
    """
    Create and return a memory manager instance.
    
    Args:
        config_path (str): Path to the configuration file
        
    Returns:
        MemoryManager: Configured memory manager instance
    """
    return MemoryManager(config_path)

# Example usage
if __name__ == "__main__":
    import datetime
    
    # Create memory manager
    memory_manager = create_memory_manager()
    
    # Store some example data
    memory_manager.store_conversation(
        agent_name="Coordinator",
        user_message="Hello, how are you?",
        agent_response="I'm doing well, thank you! How can I help you today?",
        metadata={"session_id": "123", "user_id": "user_456"}
    )
    
    # Store document (if vector store is available)
    doc_id = memory_manager.store_document(
        text="This is an example document about Python programming.",
        metadata={"topic": "programming", "language": "python"}
    )
    if doc_id:
        print(f"Stored document with ID: {doc_id}")
    else:
        print("Document storage not available (VectorStore missing)")
    
    memory_manager.add_resource(
        path="/path/to/example.py",
        resource_type="file",
        metadata={"language": "python", "purpose": "example"}
    )
    
    # Get memory stats
    stats = memory_manager.get_memory_stats()
    print("Memory Statistics:")
    for component, data in stats.items():
        print(f"  {component}: {data}")
    
    # Get agent context
    context = memory_manager.get_agent_context("Coordinator")
    print(f"\nAgent Context for Coordinator:")
    print(f"  Recent memories: {len(context['recent_memories'])}")
    print(f"  Recent conversations: {len(context['recent_conversations'])}")
    
    memory_manager.close()
