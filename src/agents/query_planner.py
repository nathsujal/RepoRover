import logging
import json
from typing import Any, Dict, List

from langchain.agents import create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool

from src.tools import (
    SemanticSearchTool,
    GraphQueryTool,
    EntityLookupTool
)
from src.memory.semantic_memory.manager import SemanticMemoryManager
from src.core.config import settings

logger = logging.getLogger(__name__)

class QueryPlannerConfig(BaseModel):
    """Configuration for the Query Planner agent."""
    model_name: str = "gemini-1.5-flash"
    agent_name: str = "query_planner"
    description: str = "Plans queries against the repository knowledge."
    temperature: float = 0.0 # Set to 0.0 for deterministic planning

class QueryPlannerAgent:
    """
    The Query Planner agent breaks down user questions into an executable plan of tool calls.
    It does NOT execute the tools itself.
    """

    def __init__(self, semantic_memory: SemanticMemoryManager):
        self.config = QueryPlannerConfig()
        self.name = self.config.agent_name
        self.description = self.config.description
        self.semantic_memory = semantic_memory
        
        tools = self.create_query_planner_tools(self.semantic_memory)

        llm = ChatGoogleGenerativeAI(
            model=self.config.model_name,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=self.config.temperature,
            model_kwargs={"response_mime_type": "application/json"}  # Fixed: removed 's'
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        self.agent_runnable = create_tool_calling_agent(llm, tools, prompt)
        logger.info(f"{self.name} agent initialized for planning only.")

    def _get_system_prompt(self) -> str:
        """
        Get the strict system prompt for the agent to force plan generation
        in a specific JSON format.
        """
        return """You are a highly specialized planning agent. Your sole purpose is to analyze a user's question about a codebase and generate a sequence of tool calls to gather the necessary information.

**CRITICAL INSTRUCTIONS:**
1.  **DO NOT answer the user's question directly.**
2.  **YOU MUST ONLY respond with a valid JSON object.**
3.  The JSON object must conform to the specified `OUTPUT FORMAT`.
4.  If you cannot determine a tool to call, respond with a JSON object containing an empty "plan" list.

**AVAILABLE TOOLS:**
- `semantic_search`: Use for broad, conceptual searches.
- `graph_query`: Use to explore relationships between known code entities.
- `entity_lookup`: Use to retrieve the full source code of a specific entity.

**OUTPUT FORMAT:**
You must respond with a JSON object with a single key, "plan".
The value of "plan" must be a list of JSON objects, where each object represents a single step in the plan.
Each step object must have two keys:
- "tool": A string representing the name of the tool to call.
- "tool_input": An object containing the arguments for the tool.

**EXAMPLE:**
User Question: "How does the 'process_data' function work?"
Your Response (JSON):
```json
{{
  "plan": [
    {{
      "tool": "code_search",
      "tool_input": {{
        "query": "def process_data"
      }}
    }},
    {{
      "tool": "graph_query",
      "tool_input": {{
        "entity_ids": ["function:utils.py:process_data"],
        "query_type": "find_callers"
      }}
    }}
  ]
}}
```"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a query plan without executing it."""
        question = input_data.get("question", "").strip()
        if not question:
            return {"status": "error", "message": "No question provided."}

        logger.info(f"Generating a query plan for question: '{question}'")
        try:
            logger.info("Performing preliminary semantic search to gather context...")
            semantic_search_tool = SemanticSearchTool(self.semantic_memory)
            search_results = await semantic_search_tool._arun(query=question, limit=5)
            
            # Format the search results into a string for the prompt
            initial_context_str = "No initial context found."
            if search_results.get("status") == "success" and search_results.get("results"):
                formatted_results = []
                for res in search_results["results"]:
                    content = res.get("content", "").strip().replace('\n', ' ')
                    entity_id = content.split(': ')[0].strip()
                    content = content.split(': ')[1].strip()
                    formatted_results.append(f"- Entity: {entity_id}\nContent: {content}\n")
                initial_context_str = "\n".join(formatted_results)
            
            logger.info(f"Initial context gathered:\n{initial_context_str}")

            agent_output = await self.agent_runnable.ainvoke({
                "input": question,
                "initial_context": initial_context_str,
                "intermediate_steps": [],
            })
            
            logger.info(f"Raw agent output after context enrichment: {agent_output}")

            # Extract the JSON output from the agent response
            json_output = agent_output.return_values["output"]
            
            # Parse the JSON string to get the plan
            plan_data = json.loads(json_output)
            plan = plan_data["plan"]

            print("\nGenerated Plan:")
            print(json.dumps(plan, indent=2))
            print()

            if not plan:
                logger.warning("Agent generated an empty plan.")
                return {"status": "error", "message": "The agent could not determine a plan of action."}

            logger.info(f"Successfully generated plan with {len(plan)} steps.")
            return {"status": "success", "plan": plan}
            
        except KeyError as e:
            logger.error(f"Missing expected key in agent output: {e}")
            return {"status": "error", "message": f"Invalid agent response structure: missing {e}"}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return {"status": "error", "message": "Failed to parse JSON response from agent"}
        except Exception as e:
            logger.exception(f"Error generating plan for question: '{question}'")
            return {"status": "error", "message": str(e)}

    def create_query_planner_tools(self, semantic_memory: SemanticMemoryManager) -> List[BaseTool]:
        """Factory function to create all query planner tools."""
        return [
            SemanticSearchTool(semantic_memory),
            GraphQueryTool(semantic_memory),
            EntityLookupTool(semantic_memory)
        ]