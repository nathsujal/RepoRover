"""
Memory system for the RepoRover agent.

This module provides a comprehensive memory system with multiple components:
- CoreMemory: Static configuration and persona
- EpisodicMemory: Conversation history and experiences
- VectorStore: Semantic search and document retrieval
- Neo4jGraphDB: Knowledge graph and relationships using Neo4j
- ResourceMemory: File and resource tracking
- MemoryManager: Unified interface for all memory components
"""

from dataclasses import asdict
import datetime
from core_memory import CoreMemory
from episodic_memory import EpisodicMemory, MemoryEntry
from vector_store import VectorStore
from graph_db import Neo4jGraphMemory
from resource_memory import ResourceMemory, Resource
import logging

logger = logging.getLogger(__name__)

__all__ = [
    'CoreMemory',
    'EpisodicMemory', 
    'MemoryEntry',
    'VectorStore',
    'Neo4jGraphMemory',
    'ResourceMemory',
    'Resource',
    'MemoryManager'
]

class MemoryManager:
    """
    Unified memory manager that coordinates all memory components.
    Provides a high-level interface for memory operations.
    """
    
    def __init__(self, config_path: str = "memory/config.yaml", 
                 neo4j_uri: str = "neo4j://127.0.0.1:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "password"):
        """
        Initialize the memory manager with all components.
        
        Args:
            config_path (str): Path to the configuration file
            neo4j_uri (str): Neo4j database URI
            neo4j_user (str): Neo4j username
            neo4j_password (str): Neo4j password
        """
        # Initialize all memory components
        self.core_memory = CoreMemory(config_path)
        self.episodic_memory = EpisodicMemory()
        self.vector_store = VectorStore()
        self.resource_memory = ResourceMemory()
        
        # Initialize Neo4j Graph Memory with error handling
        try:
            self.graph_memory = Neo4jGraphMemory(
                uri=neo4j_uri,
                user=neo4j_user, 
                password=neo4j_password
            )
            logger.info("Neo4j Graph Memory initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Neo4j Graph Memory: {e}")
            self.graph_memory = None
        
        # Track memory usage and performance
        self._access_count = 0
        self._last_cleanup = None
    
    def build_repository_graph(self, repo_path: str) -> dict:
        """
        Build a knowledge graph from a repository.
        
        Args:
            repo_path (str): Path to the repository to analyze
            
        Returns:
            dict: Build status and statistics
        """
        if not self.graph_memory:
            return {
                'status': 'error',
                'message': 'Neo4j Graph Memory not available'
            }
        
        try:
            self.graph_memory.build_repository_graph(repo_path)
            stats = self.graph_memory.get_graph_statistics()
            
            return {
                'status': 'success',
                'message': f'Repository graph built successfully',
                'statistics': stats
            }
        except Exception as e:
            logger.error(f"Failed to build repository graph: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def query_code_relationships(self, query_type: str, entity_name: str) -> list:
        """
        Query code relationships using the graph database.
        
        Args:
            query_type (str): Type of query (function_callers, function_callees, etc.)
            entity_name (str): Name of the entity to query
            
        Returns:
            list: Query results
        """
        if not self.graph_memory:
            logger.warning("Neo4j Graph Memory not available for querying")
            return []
        
        try:
            return self.graph_memory.querier.find_code_relationships(query_type, entity_name)
        except Exception as e:
            logger.error(f"Failed to query code relationships: {e}")
            return []
    
    def find_function_dependencies(self, function_name: str, max_depth: int = 3) -> list:
        """
        Find all functions that a given function depends on.
        
        Args:
            function_name (str): Name of the function
            max_depth (int): Maximum depth to search
            
        Returns:
            list: List of dependencies
        """
        if not self.graph_memory:
            return []
        
        try:
            return self.graph_memory.querier.find_function_dependencies(function_name, max_depth)
        except Exception as e:
            logger.error(f"Failed to find function dependencies: {e}")
            return []
    
    def find_circular_dependencies(self) -> list:
        """
        Find circular import dependencies in the codebase.
        
        Returns:
            list: List of files with circular dependencies
        """
        if not self.graph_memory:
            return []
        
        try:
            return self.graph_memory.querier.find_circular_dependencies()
        except Exception as e:
            logger.error(f"Failed to find circular dependencies: {e}")
            return []
    
    def find_orphaned_functions(self) -> list:
        """
        Find functions that are never called.
        
        Returns:
            list: List of orphaned functions
        """
        if not self.graph_memory:
            return []
        
        try:
            return self.graph_memory.querier.find_orphaned_functions()
        except Exception as e:
            logger.error(f"Failed to find orphaned functions: {e}")
            return []
    
    def get_file_impact_analysis(self, file_path: str, max_depth: int = 5) -> list:
        """
        Find all files that would be affected if this file changes.
        
        Args:
            file_path (str): Path to the file
            max_depth (int): Maximum depth to search
            
        Returns:
            list: List of affected files
        """
        if not self.graph_memory:
            return []
        
        try:
            return self.graph_memory.querier.get_file_impact_analysis(file_path, max_depth)
        except Exception as e:
            logger.error(f"Failed to get file impact analysis: {e}")
            return []
    
    def search_code(self, search_term: str, limit: int = 20) -> list:
        """
        Search for code elements related to a search term.
        
        Args:
            search_term (str): Term to search for
            limit (int): Maximum number of results
            
        Returns:
            list: Search results
        """
        if not self.graph_memory:
            return []
        
        try:
            return self.graph_memory.querier.find_related_code(search_term, limit)
        except Exception as e:
            logger.error(f"Failed to search code: {e}")
            return []
    
    def get_graph_statistics(self) -> dict:
        """
        Get comprehensive statistics about the knowledge graph.
        
        Returns:
            dict: Graph statistics
        """
        if not self.graph_memory:
            return {
                'status': 'not_available',
                'message': 'Neo4j Graph Memory not initialized'
            }
        
        try:
            return self.graph_memory.get_graph_statistics()
        except Exception as e:
            logger.error(f"Failed to get graph statistics: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def print_graph_statistics(self):
        """
        Print formatted graph statistics.
        """
        if not self.graph_memory:
            print("Neo4j Graph Memory not available")
            return
        
        try:
            self.graph_memory.print_graph_statistics()
        except Exception as e:
            logger.error(f"Failed to print graph statistics: {e}")
    
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
            logger.warning("Cannot store document - VectorStore not available")
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
            logger.warning("Cannot search documents - VectorStore not available")
            return []
        
        return self.vector_store.search(query, n_results=n_results)
    
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
    
    def search_memories(self, query: str, limit: int = 20) -> dict:
        """
        Search across all memory types.
        
        Args:
            query (str): Search query
            limit (int): Number of results to return
            
        Returns:
            dict: Combined search results from all memory components
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
        
        if self.graph_memory:
            results['code'] = self.search_code(query, limit)
        else:
            results['code'] = []
        
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
        
        if self.graph_memory:
            stats['graph_memory'] = self.get_graph_statistics()
        else:
            stats['graph_memory'] = {'status': 'not_available'}
        
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
        
        context = {
            'agent_config': agent_config,
            'recent_memories': [asdict(memory) for memory in recent_memories],
            'recent_conversations': recent_conversations,
            'popular_resources': [asdict(resource) for resource in popular_resources],
            'memory_stats': self.get_memory_stats()
        }
        
        # Add graph statistics if available
        if self.graph_memory:
            context['graph_stats'] = self.get_graph_statistics()
        
        return context
    
    def close(self):
        """Close all memory connections."""
        if self.graph_memory and hasattr(self.graph_memory, 'close'):
            self.graph_memory.close()

# Convenience function to create a memory manager instance
def create_memory_manager(config_path: str = "memory/config.yaml",
                         neo4j_uri: str = "neo4j://127.0.0.1:7687",
                         neo4j_user: str = "neo4j", 
                         neo4j_password: str = "password") -> MemoryManager:
    """
    Create and return a memory manager instance.
    
    Args:
        config_path (str): Path to the configuration file
        neo4j_uri (str): Neo4j database URI
        neo4j_user (str): Neo4j username  
        neo4j_password (str): Neo4j password
        
    Returns:
        MemoryManager: Configured memory manager instance
    """
    return MemoryManager(
        config_path=config_path,
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password
    )

# Example usage
if __name__ == "__main__":
    import datetime
    
    # Create memory manager
    memory_manager = create_memory_manager()
    
    # Build repository graph
    repo_path = "/home/sujalnath/dev/projects/RepoRover"
    build_result = memory_manager.build_repository_graph(repo_path)
    print(f"Repository graph build result: {build_result}")
    
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
    
    # Search for code
    code_results = memory_manager.search_code("function", limit=5)
    print(f"Found {len(code_results)} code-related results")
    
    # Find function dependencies
    dependencies = memory_manager.find_function_dependencies("main")
    print(f"Found {len(dependencies)} dependencies for 'main' function")
    
    # Get memory stats
    stats = memory_manager.get_memory_stats()
    print("Memory Statistics:")
    for component, data in stats.items():
        print(f"  {component}: {data}")
    
    # Print graph statistics
    memory_manager.print_graph_statistics()
    
    # Get agent context
    context = memory_manager.get_agent_context("Coordinator")
    print(f"\nAgent Context for Coordinator:")
    print(f"  Recent memories: {len(context['recent_memories'])}")
    print(f"  Recent conversations: {len(context['recent_conversations'])}")
    
    memory_manager.close()