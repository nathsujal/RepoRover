# RepoRover

A multi-agent system that ingests a GitHub repository, analyzes its codebase and documentation, and answers your questions about it in natural language.

---

## 🚀 Features

-   **Ingest Any Public GitHub Repo**: Simply provide a URL to start the analysis.
-   **Dual-Pronged Analysis**: Understands both the semantic meaning of documentation (what it's about) and the structural complexity of the code (how it works).
-   **Multi-Agent Architecture**: Uses a team of specialized AI agents for distinct tasks like parsing, structuring, and synthesizing information.
-   **Hybrid Memory System**: Leverages both Vector Memory for semantic search and Graph Memory for relationship analysis.
-   **Natural Language Q&A**: Ask complex questions about the codebase and get clear, context-aware answers.
-   **API-First Design**: All functionality is exposed via a clean FastAPI interface.

---

## 🏛️ Architecture Overview

The system is built on a two-phase pipeline: **Ingestion** and **Querying**.

### 1. Ingestion Pipeline
This is a one-time process for each repository. It takes the raw repository and converts it into a structured knowledge base.

`GitHub URL` → `Dispatcher Agent` → `(Librarian, Architect, Annotator Agents)` → `(Vector Memory + Graph Memory)`

-   **Dispatcher**: Clones the repo and routes files to the correct specialist.
-   **Librarian**: Processes documentation (`.md`, etc.) for semantic understanding.
-   **Architect**: Parses source code to build a structural graph of function calls and relationships.
-   **Annotator**: Creates natural language summaries of code blocks.

### 2. Query Pipeline
This is the real-time flow that happens every time a user asks a question.

`User Question` → `Query Planner Agent` → `(Retrieval from Memories)` → `Synthesizer Agent` → `Final Answer`

-   **Query Planner**: Analyzes the user's question and retrieves relevant context from both the Vector and Graph memories.
-   **Synthesizer**: Uses a Large Language Model (LLM) to generate a coherent answer based on the retrieved context (Retrieval-Augmented Generation).

