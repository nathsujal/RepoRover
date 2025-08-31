"""
Query Planner Agent: Breaks down user questions into an executable plan of tool calls.
"""

import logging
import json
from typing import Any, Dict, List

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from src.tools import (
    SemanticSearchTool,
    GraphQueryTool,
    EntityLookupTool
)
from src.memory.semantic_memory.manager import SemanticMemoryManager
from src.core.config import settings

logger = logging.getLogger(__name__)

class TacticalPlan(BaseModel):
    tool: str = Field(description="The tool to be used")
    tool_input: Dict[str, Any] = Field(description="The input to the tool")
    reasoning: str = Field(description="The reasoning for the tool call")

class TacticalPlanList(BaseModel):
    plan: List[TacticalPlan] = Field(description="The plan of tactical steps")

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
        
        self.tools = self.create_query_planner_tools(self.semantic_memory)

        self.llm = ChatGoogleGenerativeAI(
            model=self.config.model_name,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=self.config.temperature,
            model_kwargs={"response_mime_type": "application/json"}
        )

        self.parser = JsonOutputParser(pydantic_object=TacticalPlanList)

        logger.info(f"{self.name} agent initialized for planning only.")

    # --- Phase 1: Query Analysis & Decomposition ---
    async def _analyze_and_decompose_query(self, question: str, history: str) -> Dict[str, Any]:
        """
        Analyzes the query to determine its type and complexity, and decomposes
        complex queries into sub-questions.
        """
        logger.info("Phase 1: Analyzing and decomposing the query.")
        prompt = f"""
        Analyze the user's question about a software repository based on the conversation history.

        1.  **Classify the Query Type**: Choose the most fitting category:
            - `architecture`: For high-level questions about the structure, design, components, and relationships in the codebase.
            - `code_or_doc`: For specific questions about a particular function, class, file, or piece of documentation.

        2.  **Assess Complexity**: Is this a `simple` question (can be answered in 1-2 steps) or a `complex` one (requires multiple steps and combining information)?

        3.  **Decompose if Complex**: If the query is complex, break it down into a logical sequence of smaller, answerable sub-questions.

        **Conversation History**:
        ---
        {history}
        ---
        **User Question**: "{question}"

        **Output Format (JSON only)**:
        {{
          "query_type": "...",
          "complexity": "...",
          "sub_questions": ["..."]
        }}
        """
        response = await self.llm.ainvoke(prompt)
        try:
            analysis = json.loads(response.content)
            # If it's simple, the main question is the only sub-question
            if analysis.get("complexity") == "simple":
                analysis["sub_questions"] = [question]
            logger.info(f"Query analysis complete: {analysis}")
            return analysis
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to analyze query, treating as simple. Error: {e}")
            return {
                "query_type": "exploratory",
                "complexity": "simple",
                "sub_questions": [question]
            }

    def _get_code_or_doc_system_prompt(self, query_type: str, history: str) -> str:
        """Get the system prompt for code or documentation questions."""
        return f"""You are a specialized planning agent for code and documentation questions.

**CRITICAL INSTRUCTIONS:**
1.  **DO NOT answer the user's question directly.**
2.  **YOU MUST ONLY respond with a valid JSON object.**
3.  Your plan should follow this sequence:
    a. First, use the `semantic_search` tool to find the most relevant code snippets or documentation sections.
    b. Next, from the results of the `semantic_search`, identify the key entity IDs.
    c. Finally, use the `entity_lookup` tool to get the full details of those entities, or the `graph_query` tool to explore their relationships.

**Available Tools**:
    - semantic_search: Search for semantically similar content.
    - entity_lookup: Find entities list (ID is optional).
    - graph_query: Find relationships between entities.

**Conversation History**:
---
{history}
---

**Query Type**: {query_type}
"""

    def _get_architecture_system_prompt(self, query_type: str, history: str) -> str:
        """Get the system prompt for architecture questions."""
        return f"""You are a specialized planning agent for architecture and design questions.

**CRITICAL INSTRUCTIONS:**
1.  **DO NOT answer the user's question directly.**
2.  **YOU MUST ONLY respond with a valid JSON object.**
3.  Your plan should follow this sequence:
    a. First, use the `entity_lookup` tool to retrieve a list of all relevant entities (e.g., all classes, all functions). You can use wildcards like `class:*:*` to get all classes.
    b. Next, use the `graph_query` tool with the retrieved entity IDs to understand their relationships (e.g., find_callers, find_callees).
    c. If needed, you can use `semantic_search` on the results of the graph query to get more context.

**Available Tools**:
    - semantic_search: Search for semantically similar content.
    - entity_lookup: Find entities list (ID is optional).
    - graph_query: Find relationships between entities.

**Conversation History**:
---
{history}
---

**Query Type**: {query_type}
"""


    def _get_system_prompt(self, query_type: str, history: str) -> str:
        if query_type == "code_or_doc":
            return self._get_code_or_doc_system_prompt(query_type, history)
        elif query_type == "architecture":
            return self._get_architecture_system_prompt(query_type, history)
        else:
            raise ValueError(f"Unknown query type: {query_type}")


    # --- Phase 3: Tactical Plan Generation ---
    async def _generate_tactical_plan(self, question: str, query_type: str, history: str) -> List[Dict[str, Any]]:
        """Generates the detailed tool call plan for a single (sub-)question."""
        
        # prompt_template = ChatPromptTemplate.from_messages([
        #     ("system", self._get_system_prompt(query_type, history)),
        #     ("human", "{question}"),
        #     ("placeholder", "{agent_scratchpad}")
        # ])

        # planner = create_tool_calling_agent(self.llm, self.tools, prompt)
        # response = await planner.ainvoke({
        #     "system_prompt": self._get_system_prompt(query_type, history),
        #     "query": question,
        #     "intermediate_steps": [],
        # })

        prompt = PromptTemplate(
            template="""{system_prompt}\n\nQuery: {query}\n\n{format_instructions}""",
            input_variables=["system_prompt","query"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
            )

        chain = prompt | self.llm | self.parser
        response = await chain.ainvoke({
            "system_prompt": self._get_system_prompt(query_type, history),
            "query": question,
        })

        print("\n\nResponse: ")
        print(response)
        print("\n\n")
        
        plan = response["plan"]

        print()
        print(json.dumps(plan, indent=2))
        print()

        if not plan:
            logger.warning("Query Planner Agent generated an empty plan.")
            return {"status": "error", "message": "The agent could not determine a plan of action."}
        
        logger.info(f"Successfully generated plan with {len(plan)} steps.")
        return {"status": "success", "plan": plan}
    

    # --- Orchestrator ---
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrates the multi-phase planning process.
        """
        question = input_data.get("question", "").strip()
        history = input_data.get("conversation_history", "No history available.")

        if not question:
            return {"status": "error", "message": "No question provided."}

        # Phase 1: Analyze and Decompose
        analysis = await self._analyze_and_decompose_query(question, history)
        
        full_plan = []
        # Generate a plan for each sub-question
        for sub_question in analysis["sub_questions"]:
            # Phase 2: Identify Query type
            query_type = analysis["query_type"]
            
            # Phase 3: Generate Tactical Plan
            tactical_plan = await self._generate_tactical_plan(sub_question, query_type, history)

            logger.info(f"Tactical Plan for sub-question '{sub_question}': \n{tactical_plan}")
            
            full_plan.extend(tactical_plan['plan'])

        if not full_plan:
            return {"status": "error", "message": "The agent could not determine a plan of action."}

        logger.info(f"Successfully generated a full plan with {len(full_plan)} steps.")
        return {
            "status": "success",
            "plan": full_plan,
            "analysis": analysis
        }

    def create_query_planner_tools(self, semantic_memory: SemanticMemoryManager) -> List[BaseTool]:
        """Factory function to create all query planner tools."""
        return [
            SemanticSearchTool(semantic_memory),
            GraphQueryTool(semantic_memory),
            EntityLookupTool(semantic_memory)
        ]