"""
Query Planner Agent: Plans and executes queries against the semantic memory system.
"""
import logging
from typing import Any, Dict, List
import json

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from .tools import SemanticSearchTool, GraphQueryTool, EntityLookupTool, CodeSearchTool
from src.memory.semantic_memory.manager import SemanticMemoryManager
from src.core.config import settings

logger = logging.getLogger(__name__)

class QueryPlannerConfig(BaseModel):
    """Configuration for the Query Planner agent."""
    model_name: str = "gemini-1.5-flash"
    agent_name: str = "query_planner"
    description: str = "Plans and executes multi-step queries against the repository knowledge."
    max_iterations: int = 15
    temperature: float = 0.1

class QueryPlannerAgent:
    """
    The Query Planner agent that breaks down user questions into executable plans
    and coordinates with semantic memory to provide comprehensive answers.
    """

    def __init__(self, semantic_memory: SemanticMemoryManager):
        self.config = QueryPlannerConfig()
        self.name = self.config.agent_name
        self.description = self.config.description
        self.semantic_memory = semantic_memory

        # Initialize LLM with proper configuration
        llm = ChatGoogleGenerativeAI(
            model=self.config.model_name, 
            google_api_key=settings.GEMINI_API_KEY,
            temperature=self.config.temperature
        )

        # Initialize tools with semantic memory
        from .tools import create_query_planner_tools
        tools = create_query_planner_tools(semantic_memory)

        # Create a comprehensive prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        # Create the agent
        agent = create_tool_calling_agent(llm, tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True, 
            max_iterations=self.config.max_iterations,
            return_intermediate_steps=True,
            handle_parsing_errors=True
        )

        logger.info(f"{self.name} agent initialized with {len(tools)} tools.")

    def _get_system_prompt(self) -> str:
        """Get the comprehensive system prompt for the agent."""
        return """You are an expert code analyst and query planner for repository exploration.

Your role is to help users understand and navigate codebases by:
1. Breaking down complex questions into manageable search and analysis steps
2. Using available tools strategically to gather comprehensive information
3. Synthesizing findings into clear, actionable insights

Available Tools:
- semantic_search: Find conceptually related content (broad overview)
- code_search: Find specific code patterns or implementations (targeted search)  
- graph_query: Explore relationships between code entities (dependencies, callers, callees)
- entity_lookup: Get detailed information about specific entities (full implementation)

Query Strategy:
1. START BROAD: Use semantic_search to get an overview of relevant concepts
2. IDENTIFY ENTITIES: Extract entity IDs from search results for further investigation
3. EXPLORE RELATIONSHIPS: Use graph_query to understand how entities relate to each other
4. GET DETAILS: Use entity_lookup to examine specific implementations when needed
5. TARGETED SEARCH: Use code_search for specific patterns or functions if needed

Best Practices:
- Always start with semantic_search for context
- Look for entity IDs in search results to use with other tools
- Use graph queries to understand code flow and dependencies
- Provide concrete examples from the codebase when possible
- Synthesize information from multiple sources
- If you can't find something, suggest alternative search terms or approaches

Remember: You're helping users understand both the "what" and "why" of code structure and functionality."""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a query plan based on the user's question."""
        question = input_data.get("question", "").strip()
        if not question:
            return {
                "status": "error", 
                "message": "No question provided",
                "response": "I need a question to help you with the repository."
            }

        logger.info(f"Processing question: {question}")

        try:
            # Execute the agent with the question
            result = await self.agent_executor.ainvoke({"input": question})
            
            # Extract the response and any intermediate steps for debugging
            response = result.get("output", "I wasn't able to find a good answer to your question.")
            intermediate_steps = result.get("intermediate_steps", [])
            
            # Log intermediate steps for debugging
            if intermediate_steps:
                logger.info(f"Agent took {len(intermediate_steps)} steps to answer the question")
                for i, (action, observation) in enumerate(intermediate_steps):
                    logger.debug(f"Step {i+1}: Used {action.tool} with input: {action.tool_input}")
            
            return {
                "status": "success",
                "response": response,
                "steps_taken": len(intermediate_steps),
                "debug_info": {
                    "question": question,
                    "tools_used": [action.tool for action, _ in intermediate_steps] if intermediate_steps else []
                }
            }
            
        except Exception as e:
            logger.exception(f"Error processing question: {question}")
            error_message = str(e)
            
            # Provide more helpful error messages
            if "rate limit" in error_message.lower():
                user_message = "I'm currently experiencing rate limits. Please try again in a few moments."
            elif "timeout" in error_message.lower():
                user_message = "The query took too long to process. Please try a more specific question."
            elif "not found" in error_message.lower():
                user_message = "I couldn't find relevant information for your question. Try rephrasing or asking about a different aspect."
            else:
                user_message = "I encountered an error while processing your question. Please try rephrasing it or ask something else."
            
            return {
                "status": "error",
                "message": error_message,
                "response": user_message
            }

    def get_available_tools(self) -> List[Dict[str, str]]:
        """Return information about available tools for debugging/info purposes."""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.agent_executor.tools
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the agent and its dependencies."""
        try:
            # Test semantic memory connection
            test_search = await self.semantic_memory.vector_store.similarity_search("test", k=1)
            
            return {
                "status": "healthy",
                "tools_count": len(self.agent_executor.tools),
                "semantic_memory": "connected",
                "model": self.config.model_name
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "tools_count": len(self.agent_executor.tools) if hasattr(self, 'agent_executor') else 0
            }