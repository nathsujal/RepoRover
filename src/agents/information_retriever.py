"""
Information Retriever Agent: Executes a plan from the Query Planner to gather all the necessary information from the semantic memory.
"""

import logging
from typing import Any, Dict

from src.memory.semantic_memory.manager import SemanticMemoryManager
from src.tools import (
    SemanticSearchTool,
    GraphQueryTool,
    EntityLookupTool
)

logger = logging.getLogger(__name__)

class InformationRetrieverAgent:
    """
    The Information Retriever agent executes a plan from the Query Planner
    to gather all the necessary information from the semantic memory.
    """

    def __init__(self, semantic_memory: SemanticMemoryManager):
        self.name = "information_retriever"
        self.description = "Executes a query plan to gather information."
        self.semantic_memory = semantic_memory
        self.tools = {
            "semantic_search": SemanticSearchTool(semantic_memory),
            "graph_query": GraphQueryTool(semantic_memory),
            "entity_lookup": EntityLookupTool(semantic_memory)
        }
        logger.info(f"{self.name} agent initialized.")

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a query plan and collects the data."""
        logger.info("Executing a plan...")
        import json
        print(f"\n{json.dumps(input_data, indent=2)}\n")
        plan = input_data.get("plan")
        if not plan:
            return {"status": "error", "message": "No plan provided."}

        logger.info(f"Executing a plan with {len(plan)} steps.")
        
        collected_data = []
        for step in plan:
            tool_name = step.get("tool")
            tool_input = step.get("tool_input")
            
            if tool_name in self.tools:
                try:
                    tool_to_run = self.tools[tool_name]
                    # The `_arun` method is what BaseTool uses for async execution
                    result = await tool_to_run._arun(**tool_input)
                    collected_data.append({
                        "tool": tool_name,
                        "tool_input": tool_input,
                        "tool_output": result,
                    })
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {e}")
                    collected_data.append({
                        "tool": tool_name,
                        "tool_input": tool_input,
                        "tool_output": {"status": "error", "message": str(e)},
                    })
            else:
                logger.warning(f"Tool '{tool_name}' not found.")

        return {"status": "success", "collected_data": collected_data}