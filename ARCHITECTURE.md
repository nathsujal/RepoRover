# RepoRover System Architecture

RepoRover is a multi-agent system designed to build a deep, contextual understanding of software repositories. The architecture is centered around a **Dispatcher Agent** that orchestrates two primary, workflow-driven processes: **Ingestion** and **Querying**.

---

## Core Components

-   **Agents**: Specialized modules responsible for specific tasks like parsing code, generating summaries, or planning queries.
-   **Memory**: A collection of distinct memory systems that provide agents with both long-term knowledge and short-term conversational context.
-   **Workflows**: JSON-defined procedures that orchestrate the sequence of agent actions for a given high-level task.

---

## 1. The Ingestion Workflow

The goal of the ingestion workflow is to deconstruct a source code repository and build a comprehensive, multi-layered knowledge base within the **Semantic Memory**.

**Trigger**: A user provides a GitHub repository URL.

```mermaid
graph TD
    A[Start: GitHub URL] --> B(Dispatcher Agent);
    B --> C{Clones Repo & Scans Files};
    C --> D[Architect Agent];
    D --> E[Librarian Agent];
    E --> F[Annotator Agent];
    
    subgraph Semantic Memory
        G[Entity Store - SQLite];
        H[Knowledge Graph - NetworkX];
        I[Vector Store - ChromaDB];
    end

    D -- Creates Code Entities & Relationships --> H;
    D -- Stores Code Details --> G;
    E -- Creates Doc Chunks --> I;
    E -- Stores Doc Details --> G;
    F -- Generates Summaries --> G;
    F -- Updates Embeddings --> I;

    F --> J[End: Ingestion Complete];
```

## 2. The Query Workflow

The query workflow leverages the populated memory stores and conversational history to answer a user's question about the codebase.

**Trigger**: A user provides a question about the codebase.

```mermaid
graph TD
    A[Start: User Question] --> B(Dispatcher Agent);
    B -- Assembles Cognitive Context --> C[Query Planner Agent];
    
    subgraph Cognitive Context
        D[Episodic Memory - History];
        E[Core Memory - Persona];
    end

    D --> B;
    E --> B;
    
    C -- Creates Plan --> F[Information Retriever Agent];
    F -- Executes Plan --> G((Semantic Memory));
    G -- Returns Data --> H[Synthesizer Agent];
    H -- Generates Response --> I[End: Final Answer];
```