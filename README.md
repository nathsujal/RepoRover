# RepoRover

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68.0-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)

<p align="center">
  <img src="static/logo.svg" width="150" alt="RepoRover Logo">
</p>

RepoRover is an AI-powered codebase companion that helps you analyze and understand GitHub repositories. It provides deep insights into code quality, dependencies, and potential vulnerabilities through an intuitive chat interface.

## 🚀 Features

- **Repository Analysis**: Get comprehensive insights about any public GitHub repository
- **Interactive Chat**: Ask questions about the codebase in natural language
- **Code Understanding**: AI-powered code explanation and documentation
- **Dependency Analysis**: Identify and analyze project dependencies
- **Real-time Processing**: Monitor repository ingestion progress in real-time
- **Modern Web Interface**: Clean, responsive UI built with Tailwind CSS

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/RepoRover.git
   cd RepoRover
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory and add your API keys:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   GROQ_API_KEY=your_groq_api_key
   ```

## 🚀 Quick Start

1. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

3. Enter a GitHub repository URL and click "Analyze" to begin.

## 🏗️ Project Structure

```
RepoRover/
├── src/                    # Source code
│   ├── agents/            # AI agent implementations
│   ├── core/              # Core functionality and configurations
│   ├── memory/            # Memory management components
│   └── models/            # AI model integrations
├── static/                # Static files (CSS, JS, images)
│   ├── css/
│   └── stylesheet/
├── workflows/             # Workflow definitions
├── main.py                # FastAPI application entry point
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## 🌐 API Endpoints

- `POST /ingest`: Start ingesting a GitHub repository
- `GET /ingest/status/{task_id}`: Check the status of an ingestion task
- `POST /query`: Ask a question about the ingested repository

## 🤖 How It Works

1. **Repository Ingestion**:
   - Clones the specified GitHub repository
   - Processes the codebase to extract meaningful information
   - Builds a semantic understanding of the code structure

2. **Query Processing**:
   - Uses AI to understand natural language questions
   - Searches through the codebase for relevant information
   - Generates human-like responses based on the analysis

## 🛡️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- UI powered by [Tailwind CSS](https://tailwindcss.com/)
- Icons from [SVG Repo](https://www.svgrepo.com/)
- Fonts from [Google Fonts](https://fonts.google.com/)

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

<p align="center">
  <img src="static/logo.svg" width="200" alt="RepoRover Logo">
</p>

RepoRover is an advanced AI agent that ingests and understands GitHub repositories using a sophisticated multi-agent and hybrid memory architecture. This allows for deep, context-aware conversations about any codebase.

---

## System Architecture

RepoRover operates using a central Dispatcher Agent that orchestrates two primary, workflow-driven processes: Ingestion and Querying. The system is designed to build a deep, contextual understanding of software repositories through its multi-agent system and advanced cognitive memory architecture.

### The Agent Team

-   **Dispatcher Agent**: The central coordinator that manages user interactions and orchestrates the ingestion and query workflows.
-   **Architect Agent**: Parses Python source code to build a structural map of the repository, identifying classes, functions, and their relationships.
-   **Librarian Agent**: Reads and processes documentation files (like Markdown), splitting them into manageable chunks for semantic analysis.
-   **Annotator Agent**: Enriches the code map by generating concise, natural-language summaries for all identified functions.
-   **Information Retriever Agent**: Executes the plan generated by the Query Planner, gathering data from the various memory stores.
-   **Synthesizer Agent**: Generates the final, human-readable response, using the collected data, conversation history, and the agent's persona to craft a coherent answer.

### The Advanced Memory System

The agent's cognitive ability is powered by multiple specialized memory systems that work in concert.

| Memory Type | Purpose | Implementation |
| --- | --- | --- |
| **🧠 Core Memory** | Stores the agent's persona and core instructions, ensuring a consistent personality. | JSON file managed by a Pydantic class. |
| **💬 Episodic Memory** | A time-stamped log of all interactions, enabling conversational recall. | SQLite database. |
| **🧩 Semantic Memory** | A **hybrid** system that stores the meaning and relationships of code and documentation. | ChromaDB (Vectors) + NetworkX (Graph) + SQLite (Entities). |
| **🛠️ Procedural Memory**| Defines the step-by-step agent workflows for ingestion and querying. | JSON-defined task sequences. |

---

## 🛠️ Tech Stack

-   **API**: FastAPI, Uvicorn
-   **LLM Integration**: LangChain, Gemini
-   **Core & Episodic Memory**: Pydantic, SQLite
-   **Semantic Memory**:
    -   Vector Store: **ChromaDB**
    -   Knowledge Graph: **NetworkX**
    -   Entity Store: **SQLite**
-   **Code Parsing**: Python `ast` module

---

## 🚀 Getting Started

### Prerequisites

-   Python 3.9+
-   An environment manager (`venv` is built-in, or you can use [Poetry](https://python-poetry.org/))

### Installation

1.  Clone the repository:
    ```bash
    git clone [https://github.com/yourusername/RepoRover.git](https://github.com/yourusername/RepoRover.git)
    cd RepoRover
    ```

2.  Set up your environment and install dependencies.

    **Option A: Using `venv` (Recommended)**
    ```bash
    # Create and activate the virtual environment
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `.\venv\Scripts\activate`

    # Install dependencies
    pip install -r requirements.txt
    ```

    **Option B: Using Poetry**
    ```bash
    # Install dependencies
    poetry install
    ```

3.  Set up environment variables:
    ```bash
    cp .env.example .env
    # Edit .env with your configuration, including your GEMINI_API_KEY
    ```