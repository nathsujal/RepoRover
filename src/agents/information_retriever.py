"""
Information Retriever Agent: Executes a plan from the Query Planner to gather all the necessary information from the semantic memory using an intelligent LangChain agent.
"""

import logging
from typing import Any, Dict

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from src.memory.semantic_memory.manager import SemanticMemoryManager
from src.tools import (
    SemanticSearch,
    FindNodes,
    FindCallers,
    FindCallees,
    GetEntityById,
    GetEntitiesByType,
    GetAllEntities,
    GetEntitycode,
)
from src.core.config import settings

logger = logging.getLogger(__name__)

class InformationRetrieverAgent:
    """
    The Information Retriever agent uses a LangChain agent to intelligently
    reason and execute a series of tool calls to answer a user's question.
    """

    def __init__(self, semantic_memory: SemanticMemoryManager):
        self.name = "information_retriever"
        self.description = "Executes a series of tool calls to gather information."
        self.semantic_memory = semantic_memory
        self.tools = [
            SemanticSearch(semantic_memory),
            FindNodes(semantic_memory),
            FindCallers(semantic_memory),
            FindCallees(semantic_memory),
            GetEntityById(semantic_memory),
            GetEntitiesByType(semantic_memory),
            GetAllEntities(semantic_memory),
            GetEntitycode(semantic_memory),
        ]
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.0
        )
        logger.info(f"{self.name} agent initialized.")

    def _get_system_prompt(self) -> str:
        """Creates the system prompt for the executor agent."""
        return """You are a specialized information retrieval agent for a software repository. Your goal is to answer the user's question by calling a sequence of tools to gather information.

**CRITICAL STRATEGY for Answering Architectural Questions:**
1.  **ALWAYS START** by getting a list of the main components. The best tool for this is `get_entities_by_type` with the `entity_type` set to `'class'`. If that returns nothing, try again with `'function'`. This gives you the building blocks of the system.
2.  **DO NOT start with `semantic_search`** for architectural questions. Only use it if the user asks for high-level concepts or documentation.
3.  **USE THE OUTPUTS:** Once you have a list of component IDs from your first step, use those IDs as input for other tools like `find_callers` or `find_callees` to understand how they are connected.
4.  **BE PERSISTENT:** If one tool returns no results, do not give up. Analyze the user's question again and try a different tool.
5.  **FINISH STRONG:** Continue calling tools until you have gathered enough information to answer the question. Then, provide a consolidated summary of everything you found.
"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a query plan using a dedicated LangChain agent."""
        # The new approach uses the original question directly, not the pre-computed plan.
        question = input_data.get("question")
        if not question:
            analysis = input_data.get("plan_analysis", {})
            question = analysis.get("sub_questions", ["No question provided"])[0]


        logger.info(f"Information Retriever received question: '{question}'")

        # Create the LangChain agent for execution
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_tool_calling_agent(self.llm, self.tools, prompt_template)
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True, # Set to True to see the agent's thought process
            return_intermediate_steps=True,
            max_iterations=10 # Prevent infinite loops
        )

        try:
            response = await agent_executor.ainvoke({"input": question})
            
            # The intermediate steps contain the sequence of tool calls and their outputs
            collected_data = []
            for action, result in response.get("intermediate_steps", []):
                collected_data.append({
                    "tool": action.tool,
                    "tool_input": action.tool_input,
                    "tool_output": result,
                })

            return {
                "status": "success",
                "collected_data": collected_data,
                "final_output": response.get("output") # The agent's final summary
            }
        except Exception as e:
            logger.exception("An error occurred during agent execution.")
            return {"status": "error", "message": str(e)}