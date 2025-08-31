"""
Information Retriever Agent: Executes a plan from the Query Planner to gather all the necessary information from the semantic memory using an intelligent LangChain agent.
"""

import logging
import json
from typing import Any, Dict, List

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from src.memory.semantic_memory.manager import SemanticMemoryManager
from src.tools import (
    SemanticSearchTool,
    GraphQueryTool,
    EntityLookupTool
)
from src.core.config import settings

logger = logging.getLogger(__name__)

class InformationRetrieverAgent:
    """
    The Information Retriever agent uses a LangChain agent to intelligently
    execute a plan from the Query Planner.
    """

    def __init__(self, semantic_memory: SemanticMemoryManager):
        self.name = "information_retriever"
        self.description = "Executes a query plan to gather information."
        self.semantic_memory = semantic_memory
        self.tools = [
            SemanticSearchTool(semantic_memory),
            GraphQueryTool(semantic_memory),
            EntityLookupTool(semantic_memory)
        ]
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.0
        )
        logger.info(f"{self.name} agent initialized.")

    def _get_system_prompt(self) -> str:
        """Creates the system prompt for the executor agent."""
        return """You are a highly specialized execution agent. Your only purpose is to execute a given plan to gather information.

**CRITICAL INSTRUCTIONS:**
1.  You will be given an "Original Question" and an "Execution Plan" in JSON format.
2.  You MUST follow the "Execution Plan" exactly as it is written.
3.  Execute the steps in the plan sequentially using the available tools.
4.  Do NOT add, remove, or change any steps in the plan.
5.  After executing all steps, consolidate the results from each tool call into a final answer.
6.  Your final output should be the collected data from the tool calls.
"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a query plan using a dedicated LangChain agent."""
        plan = input_data.get("plan")
        # In a real scenario, the dispatcher would pass the original question.
        original_question = input_data.get("question", "No original question provided.")

        if not plan:
            return {"status": "error", "message": "No plan provided."}

        logger.info(f"Agent received a plan with {len(plan)} steps to execute.")

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
            return_intermediate_steps=True
        )

        # Format the input for the agent
        input_prompt = f"""
        Original Question: "{original_question}"

        Execution Plan:
        ```json
        {json.dumps(plan, indent=2)}
        ```

        Please execute this plan step-by-step using the available tools and gather the results.
        """

        try:
            response = await agent_executor.ainvoke({"input": input_prompt})
            
            # The intermediate steps contain the sequence of tool calls and their outputs
            collected_data = []
            for step in response.get("intermediate_steps", []):
                action, result = step
                collected_data.append({
                    "tool": action.tool,
                    "tool_input": action.tool_input,
                    "tool_output": result,
                })

            return {
                "status": "success",
                "collected_data": collected_data,
                "final_output": response.get("output")
            }
        except Exception as e:
            logger.exception("An error occurred during agent execution.")
            return {"status": "error", "message": str(e)}