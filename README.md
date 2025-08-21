# RepoRover

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An advanced AI agent that ingests and understands GitHub repositories using a sophisticated multi-agent and hybrid memory architecture, allowing for deep, context-aware conversations about any codebase.

---

## 🚀 Features

-   **Central Dispatcher**: A single, intelligent agent manages all user interactions, routing tasks for ingestion or querying.
-   **Specialized Agent Team**: A full roster of agents (Librarian, Architect, Annotator, Query Planner, etc.) handle specific, dedicated tasks.
-   **Advanced Cognitive Memory**: Goes beyond simple vector search, utilizing six distinct memory types for a more human-like understanding of context, procedures, and knowledge.
-   **Hybrid Semantic Search**: Combines a Vector Store (for conceptual meaning), a Knowledge Graph (for structural relationships), and an Entity Store (for factual details) into a powerful, unified Semantic Memory.
-   **Secure Knowledge Storage**: A dedicated, encrypted Knowledge Vault for handling sensitive information like API keys found in a repository.
-   **Procedural Workflows**: Agent tasks are defined in editable JSON workflows, making the system's procedures modular and easy to modify.

---

## 🏛️ System Architecture

The system is orchestrated by a central **Dispatcher Agent** that serves as the "front door" for all operations. It intelligently routes user input to one of two main workflows: Ingestion or Querying.



### The Advanced Memory System

The agent's cognitive ability is powered by six specialized memory systems:

| Memory Type         | Purpose                                          | Implementation                               |
| ------------------- | ------------------------------------------------ | -------------------------------------------- |
| **🧠 Core Memory** | Agent's persona and user preferences             | JSON file managed by a Pydantic class        |
| **💬 Episodic Memory** | Time-stamped log of all interactions             | SQLite database table                        |
| **🧩 Semantic Memory** | **(Hybrid)** Code/doc meaning and relationships  | ChromaDB (Vectors) + Neo4j (Graph) + SQLite (Entities) |
| **🛠️ Procedural Memory**| Step-by-step agent workflows                   | JSON-defined task sequences                  |
| **📄 Resource Memory** | Catalog of external references                 | SQLite database table                        |
| **🔐 Knowledge Vault** | Secure storage for sensitive facts & secrets     | HashiCorp Vault or an Encrypted File         |

---

## 🛠️ Tech Stack

-   **API**: FastAPI, Uvicorn
-   **Agent Orchestration**: Custom agent logic, potentially supported by LangChain
-   **Core Memory**: Pydantic, JSON/YAML
-   **Episodic & Resource Memory**: SQLite
-   **Semantic Memory**:
    -   Vector Store: **ChromaDB**
    -   Knowledge Graph: **Neo4j**
    -   Entity Details: **SQLite**
-   **Knowledge Vault**: **HashiCorp Vault** or Python **`cryptography`** library
-   **LLM Hosting & Access**: **Ollama**, **Hugging Face Transformers**, **LiteLLM**

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- [Poetry](https://python-poetry.org/) for dependency management
- [Docker](https://www.docker.com/) (for running databases like Neo4j)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/RepoRover.git
   cd RepoRover
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running the Application

Start the development server:
```bash
poetry run uvicorn main:app --reload
```

The API will be available at http://localhost:8000

### Running Tests

```bash
poetry run pytest
```

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
-   **Code Parsing**: tree-sitter