# RepoRover Memory System

A comprehensive memory system for the RepoRover agent that provides persistent storage, semantic search, and knowledge management capabilities.

## Overview

The memory system consists of five main components:

1. **CoreMemory** - Static configuration and agent personas
2. **EpisodicMemory** - Conversation history and experiences
3. **VectorStore** - Semantic search and document retrieval
4. **GraphDatabase** - Knowledge graph and relationships
5. **ResourceMemory** - File and resource tracking
6. **MemoryManager** - Unified interface for all components

## Architecture

```
MemoryManager
├── CoreMemory (YAML config)
├── EpisodicMemory (SQLite)
├── VectorStore (ChromaDB)
├── GraphDatabase (Neo4j/Mock)
└── ResourceMemory (SQLite)
```

## Installation

### Prerequisites

1. **Python 3.8+**
2. **Required packages** (already in requirements.txt):
   ```bash
   pip install chromadb sqlite-utils neo4j PyYAML
   ```

### Optional Dependencies

- **Neo4j**: For full graph database functionality
  ```bash
   pip install neo4j
   ```
  If not installed, a mock implementation will be used.

## Quick Start

### Basic Usage

```python
from memory import create_memory_manager

# Create memory manager
memory_manager = create_memory_manager()

# Store conversation
memory_id = memory_manager.store_conversation(
    agent_name="Coordinator",
    user_message="What is this repository about?",
    agent_response="This is a Python project for data analysis.",
    metadata={"session_id": "123"}
)

# Store document
doc_id = memory_manager.store_document(
    text="Python is a programming language...",
    metadata={"topic": "programming", "language": "python"}
)

# Search across all memory types
results = memory_manager.search_memories("python", limit=10)

# Get agent context
context = memory_manager.get_agent_context("Coordinator")

# Clean up
memory_manager.close()
```

### Individual Components

#### CoreMemory
```python
from memory import CoreMemory

core_memory = CoreMemory("memory/config.yaml")
agent_config = core_memory._config.get('agents', [])
```

#### EpisodicMemory
```python
from memory import EpisodicMemory

episodic = EpisodicMemory()
memory_id = episodic.store_memory(
    agent_name="Coordinator",
    event_type="conversation",
    content={"message": "Hello"},
    importance=0.8
)
```

#### VectorStore
```python
from memory import VectorStore

vector_store = VectorStore()
doc_ids = vector_store.add_documents([
    {"text": "Document content", "metadata": {"topic": "example"}}
])
results = vector_store.search("example query")
```

#### GraphDatabase
```python
from memory import GraphDatabase

graph_db = GraphDatabase()
node_id = graph_db.create_node(
    labels=["Person"],
    properties={"name": "Alice", "role": "developer"}
)
```

#### ResourceMemory
```python
from memory import ResourceMemory

resource_memory = ResourceMemory()
resource_id = resource_memory.add_resource(
    path="/path/to/file.py",
    resource_type="file",
    metadata={"language": "python"}
)
```

## Configuration

### Agent Configuration (config.yaml)

The `config.yaml` file defines agent personas and capabilities:

```yaml
agents:
  - name: Coordinator
    role: The project manager
    description: Oversees multi-agent execution
    goals:
      - Decompose complex queries
      - Assign tasks to specialized agents
    tools: []

  - name: Repo Analyst
    role: The scout
    description: Maps repository structure
    goals:
      - Traverse the repository
      - Identify key files
    tools: [graph_query_tool, resource_db_tool]
```

### Database Configuration

#### SQLite Databases
- **Episodic Memory**: `data/episodic_memory.db`
- **Resource Memory**: `data/resource_memory.db`

#### ChromaDB
- **Vector Store**: `data/vector_store/`
- **Collection**: `documents`

#### Neo4j (Optional)
- **URI**: `bolt://localhost:7687`
- **Database**: `neo4j`
- **Username**: `neo4j`
- **Password**: `password`

## API Reference

### MemoryManager

#### Core Methods

- `store_conversation(agent_name, user_message, agent_response, metadata)` - Store conversation
- `store_document(text, metadata, document_id)` - Store document in vector store
- `search_documents(query, n_results)` - Semantic search
- `create_knowledge_node(labels, properties, node_id)` - Create graph node
- `create_relationship(start_node_id, end_node_id, relationship_type, properties)` - Create relationship
- `add_resource(path, resource_type, metadata)` - Add resource
- `get_conversation_history(limit)` - Get recent conversations
- `get_agent_config(agent_name)` - Get agent configuration
- `search_memories(query, limit)` - Cross-memory search
- `get_memory_stats()` - Get comprehensive statistics
- `get_agent_context(agent_name, context_size)` - Get agent context

#### Utility Methods

- `cleanup_old_memories(days_old)` - Clean up old data
- `backup_memory(backup_dir)` - Create backups
- `close()` - Close connections

### EpisodicMemory

#### Core Methods

- `store_memory(agent_name, event_type, content, metadata, importance)` - Store memory
- `retrieve_memories(agent_name, event_type, limit, min_importance)` - Retrieve memories
- `get_conversation_history(limit)` - Get conversations
- `search_memories(query, limit)` - Search memories
- `update_importance(memory_id, new_importance)` - Update importance
- `delete_memory(memory_id)` - Delete memory
- `get_memory_stats()` - Get statistics

### VectorStore

#### Core Methods

- `add_documents(documents, metadatas, ids)` - Add documents
- `search(query, n_results, filter_metadata)` - Search documents
- `get_document(document_id)` - Get specific document
- `update_document(document_id, new_text, new_metadata)` - Update document
- `delete_document(document_id)` - Delete document
- `search_by_metadata(metadata_filter, n_results)` - Search by metadata
- `get_collection_stats()` - Get statistics
- `backup_collection(backup_path)` - Create backup
- `restore_collection(backup_path)` - Restore from backup

### GraphDatabase

#### Core Methods

- `create_node(labels, properties, node_id)` - Create node
- `get_node(node_id)` - Get node
- `update_node(node_id, properties)` - Update node
- `delete_node(node_id)` - Delete node
- `create_relationship(start_node_id, end_node_id, relationship_type, properties)` - Create relationship
- `get_relationships(node_id, direction)` - Get relationships
- `search_nodes(labels, properties, limit)` - Search nodes
- `execute_cypher(query, parameters)` - Execute custom query
- `get_graph_stats()` - Get statistics
- `create_index(label, property_name)` - Create index

### ResourceMemory

#### Core Methods

- `add_resource(path, resource_type, metadata, resource_id)` - Add resource
- `get_resource(resource_id)` - Get resource
- `get_resource_by_path(path)` - Get resource by path
- `update_resource_metadata(resource_id, metadata)` - Update metadata
- `record_access(resource_id)` - Record access
- `search_resources(query, resource_type, limit)` - Search resources
- `get_recent_resources(limit)` - Get recent resources
- `get_popular_resources(limit)` - Get popular resources
- `get_resources_by_type(resource_type, limit)` - Get by type
- `get_related_resources(resource_id, limit)` - Get related resources
- `get_resource_stats()` - Get statistics
- `cleanup_invalid_resources()` - Clean up invalid files

## Testing

Run the test script to verify all components:

```bash
cd memory
python test_memory.py
```

This will test:
- Core memory configuration
- Episodic memory storage and retrieval
- Vector store document operations
- Graph database node and relationship creation
- Resource memory tracking
- Integrated memory manager functionality
- Backup and cleanup operations

## Data Persistence

### File Structure
```
memory/
├── config.yaml              # Agent configuration

data/
├── episodic_memory.db       # Conversation history
├── resource_memory.db       # Resource tracking
├── vector_store/            # ChromaDB data
│   └── documents/          # Document collection
├── backups/                # Backup directory
└── test_backups/           # Test backups
```

### Backup and Recovery

```python
# Create backup
backup_paths = memory_manager.backup_memory("memory/backups")

# Restore from backup (individual components)
vector_store.restore_collection("data/backups/vector_20240101_120000")
```

## Performance Considerations

### Memory Usage
- **Episodic Memory**: SQLite with indexes for efficient querying
- **Vector Store**: ChromaDB with in-memory caching
- **Graph Database**: Neo4j with connection pooling
- **Resource Memory**: SQLite with optimized queries

### Optimization Tips
1. **Batch Operations**: Use batch methods when adding multiple items
2. **Indexing**: Create indexes on frequently queried fields
3. **Cleanup**: Regularly run cleanup to remove old data
4. **Connection Management**: Always close connections when done

### Scaling
- **Horizontal**: Multiple memory manager instances
- **Vertical**: Increase database resources
- **Caching**: Implement application-level caching
- **Sharding**: Split data across multiple databases

## Error Handling

The memory system includes comprehensive error handling:

```python
try:
    memory_manager = create_memory_manager()
    # ... operations
except FileNotFoundError as e:
    print(f"Configuration file not found: {e}")
except ImportError as e:
    print(f"Required dependency missing: {e}")
except Exception as e:
    print(f"Memory operation failed: {e}")
finally:
    memory_manager.close()
```

## Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**
   - Install Neo4j driver: `pip install neo4j`
   - Check Neo4j server is running
   - Verify connection credentials

2. **ChromaDB Errors**
   - Ensure ChromaDB is installed: `pip install chromadb`
   - Check disk space for vector store
   - Verify collection permissions

3. **SQLite Errors**
   - Check file permissions
   - Ensure directory exists
   - Verify database file integrity

4. **Configuration Errors**
   - Validate YAML syntax
   - Check file paths
   - Verify agent configurations

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When adding new memory components:

1. Follow the existing class structure
2. Include comprehensive docstrings
3. Add unit tests
4. Update this README
5. Include error handling
6. Add to the MemoryManager integration

## License

This memory system is part of the RepoRover project and follows the same license terms.
