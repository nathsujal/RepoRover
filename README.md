# RepoRover

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68.0-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)

<p align="center">
  <img src="static/logo.svg" width="150" alt="RepoRover Logo">
</p>

RepoRover is a technical multi-agent AI system designed to explore and analyze Python repositories on GitHub. It brings together specialized AI agents connected through a structured memory system, enabling them to share insights about code, libraries, commit history, and tooling in a coordinated way.

The project was inspired by a personal goal: to better understand Python projects and open-source tools on GitHub, while gaining hands-on experience with multi-agent architectures and memory systems.


- **🤖 Multi-Agent Collaboration**: distinct AI agents with specialized roles.
- **🧠 Structured Memory System**: modular memory components for code metadata, commit history, and user preferences.
- **🔗 Agent Communication**: coordination between agents through shared memory.
- **📂 Repository Insights**: automated exploration of project structures, libraries, and tools.
- **🔍 Research-Inspired Design**: influenced by state-of-the-art papers in agentic AI and modular memory.

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
   python main.py
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

## 📖 Research Inspiration

RepoRover’s architecture was shaped by cutting-edge research:
<a id="1">[1]</a> “Small Language Models are the Future of Agentic AI” [Belcak et al., 2025](https://arxiv.org/abs/2506.02153)
<a id="2">[2]</a> “MIRIX: A Modular Multi-Agent Memory System for Enhanced Long-Term Reasoning and Personalization in LLM-Based Agents” [2025](https://arxiv.org/abs/2507.07957)

RepoRover applies these ideas by:
- Using compact, task-specific models for agents.
- Implementing a modular memory framework inspired by MIRIX’s multi-memory design.

## 🛡️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- UI powered by [Tailwind CSS](https://tailwindcss.com/)
- Icons from [SVG Repo](https://www.svgrepo.com/)
- Fonts from [Google Fonts](https://fonts.google.com/)
