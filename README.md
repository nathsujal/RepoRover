# RepoRover

An advanced AI system designed to deeply understand and interact with software repositories through a multi-agent architecture and sophisticated hybrid memory system.

## 🎯 **Project Vision**

RepoRover moves beyond simple RAG by employing a team of specialized AI agents and a sophisticated, hybrid memory architecture. The goal is to create an assistant that can answer complex queries about a codebase by understanding the explicit structure of the code, the conceptual content of the documentation, and the critical links between them.

## 🏗️ **Core Architecture: Multi-Agent, Hybrid Memory System**

The system is built on two core principles:

* **Multi-Agent System**: Instead of a single monolithic model, the architecture uses a team of five specialized, open-source Small Language Models (SLMs). Each agent is fine-tuned for a specific role, leading to higher efficiency, speed, and accuracy. The collaboration is managed by the **CrewAI** framework.
* **Hybrid Semantic Memory**: The system's "brain" is a hybrid model that uses the best tool for each data type. This is the cornerstone of its deep understanding capabilities.

## 🤖 **The Agent Team & Technology Stack**

Each agent is a distinct specialist powered by a carefully selected open-source LLM.

| Agent Role | Responsibility | Open-Source LLM Choice |
| :--- | :--- | :--- |
| **Coordinator** | The project manager; deconstructs queries, plans tasks, and manages the workflow. | `meta-llama/Llama-3.1-70b-instruct` |
| **Repo Analyst** | The scout; performs the initial scan of a repository to build the memory. | `microsoft/Phi-3-mini-128k-instruct` |
| **Code Specialist** | The code guru; analyzes code structure, logic, and dependencies. | `meta-llama/CodeLlama-70b-hf` |
| **Docs Specialist**| The librarian; understands and retrieves information from all prose documentation. | `meta-llama/Llama-3.1-8b-instruct` |
| **Synthesizer** | The communicator; takes structured data from other agents and crafts the final response. | `mistralai/Mistral-Nemo-12B-instruct`|

## 🧠 **The Multi-Faceted Memory Architecture**

The system's memory is modeled after a cognitive architecture with six distinct components:

### **Memory Components**

1. **Core Memory**: A YAML file storing the agent's persona and user profile.
2. **Episodic Memory**: An SQLite database logging the chronological history of all actions for context and debugging.
3. **Semantic Memory (Hybrid)**:
   * **Neo4j Graph Database**: Stores the code as a **Knowledge Graph**. Nodes are files, classes, and functions; edges are relationships like `:CALLS`, `:IMPORTS`, and `:INHERITS_FROM`. This captures the explicit structure.
   * **ChromaDB Vector Store**: Stores embeddings of all documentation (`.md`, `.txt`). This captures conceptual and semantic meaning.
4. **Procedural Memory**: YAML files defining step-by-step workflows for complex, multi-agent tasks (e.g., a "full security audit").
5. **Resource Memory**: An SQLite database serving as a catalog of all files in the repository.
6. **Knowledge Vault**: A secure store (e.g., HashiCorp Vault or `.env` file) for sensitive data like API keys.

### **Storage Structure**

```
RepoRover/
├── memory/                    # Code and configuration
│   ├── config.yaml           # Agent configuration
│   ├── __init__.py           # Memory system code
│   ├── core_memory.py        # Core memory implementation
│   ├── episodic_memory.py    # Episodic memory implementation
│   ├── vector_store.py       # Vector store implementation
│   ├── graph_db.py           # Graph database implementation
│   ├── resource_memory.py    # Resource memory implementation
│   └── README.md             # Memory system documentation
│
├── data/                     # All data storage
│   ├── episodic_memory.db    # Conversation history
│   ├── resource_memory.db    # Resource tracking
│   ├── vector_store/         # ChromaDB data
│   ├── backups/              # Backup directory
│   └── test_backups/         # Test backups
│
├── agents/                   # Agent implementations
├── orchestration/            # Multi-agent orchestration
├── tools/                    # Agent tools
├── ingestions/               # Data ingestion pipelines
├── ui/                       # User interface
└── tests/                    # Test suite
```

## 🚀 **Installation & Setup**

### **Prerequisites**

- Python 3.8+
- Neo4j Database (optional, falls back to mock implementation)
- Git

### **Quick Start**

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RepoRover
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Optional: Install Neo4j**
   ```bash
   # For full graph database functionality
   pip install neo4j
   ```

5. **Run tests**
   ```bash
   python tests/test_memory.py
   ```

## 📖 **Usage Examples**

### **Basic Memory Operations**

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

### **Advanced Graph Operations**

```python
# Create knowledge graph nodes
python_node = memory_manager.create_knowledge_node(
    labels=["ProgrammingLanguage", "Technology"],
    properties={"name": "Python", "type": "language"}
)

ml_node = memory_manager.create_knowledge_node(
    labels=["Technology", "AI"],
    properties={"name": "Machine Learning", "type": "field"}
)

# Create relationships
rel_id = memory_manager.create_relationship(
    start_node_id=python_node,
    end_node_id=ml_node,
    relationship_type="USED_IN",
    properties={"frequency": "high"}
)
```

### **Resource Tracking**

```python
# Add resources
resource_id = memory_manager.add_resource(
    path="/path/to/file.py",
    resource_type="file",
    metadata={"language": "python", "purpose": "main_module"}
)

# Record access
memory_manager.resource_memory.record_access(resource_id)

# Get popular resources
popular = memory_manager.resource_memory.get_popular_resources(10)
```

## 🔄 **Key Workflows**

### **Ingestion Workflow**
When given a new GitHub URL, the **Repo Analyst** orchestrates the ingestion process:
1. Code files are parsed using `tree-sitter` to build the **Neo4j knowledge graph**
2. Documentation files are chunked, embedded, and stored in the **ChromaDB vector store**
3. File metadata is cataloged in **Resource Memory**
4. Process is logged in **Episodic Memory**

### **Interaction Workflow**
When a user asks a question, the **Coordinator** agent takes charge:

**Simple Queries**:
- Code structure queries → **Code Specialist** queries **Neo4j**
- Documentation queries → **Docs Specialist** queries **ChromaDB**

**Hybrid Queries**:
- Complex queries linking concepts to code → Multi-step plan
- First: Docs Specialist finds concept in ChromaDB
- Second: Code Specialist finds implementation in Neo4j
- Final: Synthesizer generates cohesive answer

## 🧪 **Testing**

### **Run All Tests**
```bash
python tests/test_memory.py
```

### **Test Individual Components**
```python
# Test memory system
from memory import create_memory_manager
memory_manager = create_memory_manager()

# Test specific functionality
stats = memory_manager.get_memory_stats()
print(stats)
```

### **Memory System Tests**
The test suite covers:
- ✅ Core memory configuration
- ✅ Episodic memory storage and retrieval
- ✅ Vector store document operations
- ✅ Graph database node and relationship creation
- ✅ Resource memory tracking
- ✅ Integrated memory manager functionality
- ✅ Backup and cleanup operations

## 📊 **Performance & Monitoring**

### **Memory Statistics**
```python
stats = memory_manager.get_memory_stats()
# Returns comprehensive statistics for all components
```

### **Backup & Recovery**
```python
# Create backup
backup_paths = memory_manager.backup_memory("data/backups")

# Restore from backup
vector_store.restore_collection("data/backups/vector_20240101_120000")
```

### **Cleanup Operations**
```python
# Clean up old memories
cleanup_stats = memory_manager.cleanup_old_memories(days_old=30)

# Clean up invalid resources
cleaned = memory_manager.resource_memory.cleanup_invalid_resources()
```

## 🔧 **Configuration**

### **Agent Configuration** (`memory/config.yaml`)
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

### **Database Configuration**
- **SQLite Databases**: `data/episodic_memory.db`, `data/resource_memory.db`
- **ChromaDB**: `data/vector_store/`
- **Neo4j**: `bolt://localhost:7687` (optional)

## 🛠️ **Development**

### **Adding New Memory Components**
1. Follow the existing class structure
2. Include comprehensive docstrings
3. Add unit tests
4. Update documentation
5. Include error handling
6. Add to the MemoryManager integration

### **Debugging**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use debug script
python memory/debug_graph.py
```

## 📈 **Scaling Considerations**

- **Horizontal**: Multiple memory manager instances
- **Vertical**: Increase database resources
- **Caching**: Implement application-level caching
- **Sharding**: Split data across multiple databases

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Follow the existing code style
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 **Troubleshooting**

### **Common Issues**

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

For more detailed troubleshooting, see the [Memory System README](memory/README.md).