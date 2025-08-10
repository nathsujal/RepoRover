# RepoRover

### **1. Project Vision**

The objective is to build **AgenticAI-RepoRover**, an advanced AI system designed to deeply understand and interact with software repositories. The system moves beyond simple RAG by employing a team of specialized AI agents and a sophisticated, hybrid memory architecture. The goal is to create an assistant that can answer complex queries about a codebase by understanding the explicit structure of the code, the conceptual content of the documentation, and the critical links between them.


### **2. Core Architecture: A Multi-Agent, Hybrid Memory System**

The system is built on two core principles:

* **Multi-Agent System**: Instead of a single monolithic model, the architecture uses a team of five specialized, open-source Small Language Models (SLMs). Each agent is fine-tuned for a specific role, leading to higher efficiency, speed, and accuracy. The collaboration is managed by the **CrewAI** framework.
* **Hybrid Semantic Memory**: The system's "brain" is a hybrid model that uses the best tool for each data type. This is the cornerstone of its deep understanding capabilities.


### **3. The Agent Team & Technology Stack**

Each agent is a distinct specialist powered by a carefully selected open-source LLM.

| Agent Role | Responsibility | Open-Source LLM Choice |
| :--- | :--- | :--- |
| **Coordinator** | The project manager; deconstructs queries, plans tasks, and manages the workflow. | `meta-llama/Llama-3.1-70b-instruct` |
| **Repo Analyst** | The scout; performs the initial scan of a repository to build the memory. | `microsoft/Phi-3-mini-128k-instruct` |
| **Code Specialist** | The code guru; analyzes code structure, logic, and dependencies. | `meta-llama/CodeLlama-70b-hf` |
| **Docs Specialist**| The librarian; understands and retrieves information from all prose documentation. | `meta-llama/Llama-3.1-8b-instruct` |
| **Synthesizer** | The communicator; takes structured data from other agents and crafts the final response. | `mistralai/Mistral-Nemo-12B-instruct`|


### **4. The Multi-Faceted Memory Architecture**

The system's memory is modeled after a cognitive architecture with six distinct components:

1.  **Core Memory**: A YAML file storing the agent's persona and user profile.
2.  **Episodic Memory**: An SQLite database logging the chronological history of all actions for context and debugging.
3.  **Semantic Memory (Hybrid)**:
    * **Neo4j Graph Database**: Stores the code as a **Knowledge Graph**. Nodes are files, classes, and functions; edges are relationships like `:CALLS`, `:IMPORTS`, and `:INHERITS_FROM`. This captures the explicit structure.
    * **ChromaDB Vector Store**: Stores embeddings of all documentation (`.md`, `.txt`). This captures conceptual and semantic meaning.
4.  **Procedural Memory**: YAML files defining step-by-step workflows for complex, multi-agent tasks (e.g., a "full security audit").
5.  **Resource Memory**: An SQLite database serving as a catalog of all files in the repository.
6.  **Knowledge Vault**: A secure store (e.g., HashiCorp Vault or `.env` file) for sensitive data like API keys.


### **5. Key Workflows**

The system operates via two primary workflows:

* **Ingestion Workflow**: When given a new GitHub URL, the **Repo Analyst** orchestrates the ingestion process.
    * Code files are parsed using `tree-sitter` to build the **Neo4j knowledge graph**.
    * Documentation files are chunked, embedded, and stored in the **ChromaDB vector store**.
* **Interaction Workflow**: When a user asks a question, the **Coordinator** agent takes charge.
    * **Simple Queries**: If the query is purely about code structure ("What calls this function?"), it tasks the **Code Specialist** to query **Neo4j**. If it's about documentation ("How do I contribute?"), it tasks the **Docs Specialist** to query **ChromaDB**.
    * **Hybrid Queries**: For complex queries linking concepts to code ("Show me the code that implements the 'rate-limiting' feature mentioned in the docs"), the Coordinator creates a multi-step plan. It first tasks the Docs Specialist to find the concept in ChromaDB, then uses the output to inform a second task for the Code Specialist to find the relevant implementation in Neo4j.

Finally, all retrieved context is passed to the **Synthesizer Agent** to generate a single, cohesive answer. The entire process is designed to be observable and debuggable using a tool like **Langfuse**. The user interface is built with **Streamlit**.