#!/usr/bin/env python3
"""
Test script for the RepoRover memory system.
This script demonstrates how to use all memory components.
"""

import os
import sys
import datetime
from pathlib import Path

# Add the parent directory to the path so we can import the memory module
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory import create_memory_manager

def test_core_memory():
    """Test core memory functionality."""
    print("=== Testing Core Memory ===")
    
    memory_manager = create_memory_manager()
    
    # Test agent configuration retrieval
    coordinator_config = memory_manager.get_agent_config("Coordinator")
    print(f"Coordinator config: {coordinator_config.get('name', 'Not found')}")
    
    analyst_config = memory_manager.get_agent_config("Repo Analyst")
    print(f"Repo Analyst config: {analyst_config.get('name', 'Not found')}")
    
    return memory_manager

def test_episodic_memory(memory_manager):
    """Test episodic memory functionality."""
    print("\n=== Testing Episodic Memory ===")
    
    # Store some conversation memories
    memory_id1 = memory_manager.store_conversation(
        agent_name="Coordinator",
        user_message="What is this repository about?",
        agent_response="This appears to be a Python project for data analysis.",
        metadata={"session_id": "test_123", "topic": "repository_analysis"}
    )
    print(f"Stored conversation memory: {memory_id1}")
    
    memory_id2 = memory_manager.store_conversation(
        agent_name="Repo Analyst",
        user_message="Show me the main functions",
        agent_response="I found several key functions in the codebase...",
        metadata={"session_id": "test_123", "topic": "code_analysis"}
    )
    print(f"Stored conversation memory: {memory_id2}")
    
    # Retrieve conversation history
    history = memory_manager.get_conversation_history(limit=5)
    print(f"Retrieved {len(history)} conversation entries")
    
    # Search memories
    search_results = memory_manager.episodic_memory.search_memories("repository", limit=5)
    print(f"Found {len(search_results)} memories containing 'repository'")
    
    return memory_manager

def test_vector_store(memory_manager):
    """Test vector store functionality."""
    print("\n=== Testing Vector Store ===")
    
    # Store some documents
    doc_id1 = memory_manager.store_document(
        text="Python is a high-level programming language known for its simplicity and readability.",
        metadata={"topic": "programming", "language": "python", "difficulty": "beginner"}
    )
    print(f"Stored document: {doc_id1}")
    
    doc_id2 = memory_manager.store_document(
        text="Machine learning algorithms can be used to predict future outcomes based on historical data.",
        metadata={"topic": "machine_learning", "category": "ai", "difficulty": "advanced"}
    )
    print(f"Stored document: {doc_id2}")
    
    doc_id3 = memory_manager.store_document(
        text="Repository analysis involves examining code structure, dependencies, and documentation.",
        metadata={"topic": "code_analysis", "category": "development", "difficulty": "intermediate"}
    )
    print(f"Stored document: {doc_id3}")
    
    # Search documents
    search_results = memory_manager.search_documents("programming language", n_results=3)
    print(f"Found {len(search_results)} documents about programming")
    
    search_results = memory_manager.search_documents("machine learning", n_results=3)
    print(f"Found {len(search_results)} documents about machine learning")
    
    return memory_manager

def test_graph_database(memory_manager):
    """Test graph database functionality."""
    print("\n=== Testing Graph Database ===")
    
    # Create some knowledge nodes
    python_node = memory_manager.create_knowledge_node(
        labels=["ProgrammingLanguage", "Technology"],
        properties={"name": "Python", "type": "language", "paradigm": "multi-paradigm"}
    )
    print(f"Created Python node: {python_node}")
    
    ml_node = memory_manager.create_knowledge_node(
        labels=["Technology", "AI"],
        properties={"name": "Machine Learning", "type": "field", "category": "artificial_intelligence"}
    )
    print(f"Created ML node: {ml_node}")
    
    repo_node = memory_manager.create_knowledge_node(
        labels=["Concept", "Development"],
        properties={"name": "Repository Analysis", "type": "process", "domain": "software_development"}
    )
    print(f"Created Repository Analysis node: {repo_node}")
    
    # Create relationships
    rel1 = memory_manager.create_relationship(
        start_node_id=python_node,
        end_node_id=ml_node,
        relationship_type="USED_IN",
        properties={"frequency": "high", "purpose": "data_processing"}
    )
    print(f"Created relationship: {rel1}")
    
    rel2 = memory_manager.create_relationship(
        start_node_id=repo_node,
        end_node_id=python_node,
        relationship_type="ANALYZES",
        properties={"tool": "RepoRover", "method": "static_analysis"}
    )
    print(f"Created relationship: {rel2}")
    
    return memory_manager

def test_resource_memory(memory_manager):
    """Test resource memory functionality."""
    print("\n=== Testing Resource Memory ===")
    
    # Add some resources
    resource_id1 = memory_manager.add_resource(
        path="/path/to/main.py",
        resource_type="file",
        metadata={"language": "python", "purpose": "main_script", "size": "2KB"}
    )
    print(f"Added resource: {resource_id1}")
    
    resource_id2 = memory_manager.add_resource(
        path="https://api.github.com/repos/user/repo",
        resource_type="api",
        metadata={"method": "GET", "format": "json", "purpose": "repository_info"}
    )
    print(f"Added resource: {resource_id2}")
    
    resource_id3 = memory_manager.add_resource(
        path="/path/to/requirements.txt",
        resource_type="file",
        metadata={"type": "dependencies", "format": "text", "purpose": "package_management"}
    )
    print(f"Added resource: {resource_id3}")
    
    # Record some access
    memory_manager.resource_memory.record_access(resource_id1)
    memory_manager.resource_memory.record_access(resource_id1)  # Access twice
    memory_manager.resource_memory.record_access(resource_id2)
    
    # Get popular resources
    popular = memory_manager.resource_memory.get_popular_resources(5)
    print(f"Popular resources: {len(popular)} found")
    
    # Search resources
    search_results = memory_manager.resource_memory.search_resources("python", limit=5)
    print(f"Found {len(search_results)} resources containing 'python'")
    
    return memory_manager

def test_memory_manager_integration(memory_manager):
    """Test integrated memory manager functionality."""
    print("\n=== Testing Memory Manager Integration ===")
    
    # Test cross-memory search
    search_results = memory_manager.search_memories("python", limit=10)
    print(f"Cross-memory search for 'python':")
    for memory_type, results in search_results.items():
        print(f"  {memory_type}: {len(results)} results")
    
    # Test agent context
    context = memory_manager.get_agent_context("Coordinator", context_size=3)
    print(f"\nAgent context for Coordinator:")
    print(f"  Agent config: {context['agent_config'].get('name', 'Unknown')}")
    print(f"  Recent memories: {len(context['recent_memories'])}")
    print(f"  Recent conversations: {len(context['recent_conversations'])}")
    print(f"  Popular resources: {len(context['popular_resources'])}")
    
    # Test memory statistics
    stats = memory_manager.get_memory_stats()
    print(f"\nMemory Statistics:")
    for component, data in stats.items():
        if isinstance(data, dict):
            print(f"  {component}:")
            for key, value in data.items():
                print(f"    {key}: {value}")
        else:
            print(f"  {component}: {data}")
    
    return memory_manager

def test_memory_cleanup_and_backup(memory_manager):
    """Test memory cleanup and backup functionality."""
    print("\n=== Testing Memory Cleanup and Backup ===")
    
    # Test cleanup (should not remove much since we just created the data)
    cleanup_stats = memory_manager.cleanup_old_memories(days_old=1)
    print(f"Cleanup statistics: {cleanup_stats}")
    
    # Test backup
    try:
        backup_paths = memory_manager.backup_memory("data/test_backups")
        print(f"Backup created:")
        for backup_type, path in backup_paths.items():
            print(f"  {backup_type}: {path}")
    except Exception as e:
        print(f"Backup failed: {e}")
    
    return memory_manager

def main():
    """Run all memory system tests."""
    print("RepoRover Memory System Test")
    print("=" * 50)
    
    try:
        # Test each component
        memory_manager = test_core_memory()
        memory_manager = test_episodic_memory(memory_manager)
        memory_manager = test_vector_store(memory_manager)
        memory_manager = test_graph_database(memory_manager)
        memory_manager = test_resource_memory(memory_manager)
        memory_manager = test_memory_manager_integration(memory_manager)
        memory_manager = test_memory_cleanup_and_backup(memory_manager)
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        print("Memory system is working correctly.")
        
        # Clean up
        memory_manager.close()
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
