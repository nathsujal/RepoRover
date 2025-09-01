"""
A collection of fine-grained tools for the Query Planner Agent to interact
with the different components of semantic memory. Each tool has a single,
well-defined purpose to avoid confusing the AI agent.
"""
from typing import Any, Dict, List, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import logging
import asyncio

logger = logging.getLogger(__name__)

# ==============================================================================
# Tool 1: Semantic Search (Vector Store)
# ==============================================================================

class SemanticSearchInput(BaseModel):
    """Input schema for semantic search."""
    query: str = Field(description="The search query to find semantically similar content")
    limit: int = Field(default=10, description="Maximum number of results to return")


class SemanticSearch(BaseTool):
    """
    Searches docs and code summaries for concepts semantically similar to the query.
    This is the best tool for broad, conceptual searches or when you don't know the
    exact name or ID of what you're looking for.
    """
    name: str = "semantic_search"
    description: str = (
        "Searches docs and code summaries for concepts semantically similar to the query. "
        "Best for broad, conceptual searches to get an overview of relevant entities."
    )
    args_schema: type[BaseModel] = SemanticSearchInput

    def __init__(self, semantic_memory, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_semantic_memory', semantic_memory)

    @property
    def semantic_memory(self):
        return self._semantic_memory

    def _run(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Synchronous execution wrapper for the tool."""
        # This is a simple way to run the async method in a sync context.
        return asyncio.run(self._arun(query, limit))

    async def _arun(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Async implementation of the tool."""
        try:
            logger.info(f"Performing semantic search for: '{query}' (limit: {limit})")
            search_results = await self.semantic_memory.vector_store.similarity_search_with_score(query, k=limit)
            
            formatted_results = []
            for doc, score in search_results:
                metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                if 'id' not in metadata:
                    metadata['entity_id'] = doc.id
                
                formatted_results.append({
                    "content": doc.content,
                    "metadata": metadata,
                    "similarity_score": float(score)
                })
            
            logger.info(f"Found {len(formatted_results)} semantic matches")
            return {"status": "success", "results": formatted_results}
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return {"status": "error", "error": str(e)}

# ==============================================================================
# Tool 2: Find Nodes in Graph
# ==============================================================================

class FindNodesInput(BaseModel):
    """Input schema for finding nodes in the graph."""
    labels: Optional[List[str]] = Field(default=None, description="A list of node types (labels) to search for, e.g., ['function', 'class'].")
    properties: Optional[Dict[str, Any]] = Field(default=None, description="A dictionary of properties to filter nodes by.")

class FindNodes(BaseTool):
    """
    Finds nodes in the knowledge graph based on their type (label) and/or properties.
    Useful for getting a list of all functions, classes, or nodes that match
    specific criteria.
    """
    name: str = "find_nodes"
    description: str = "Finds nodes in the knowledge graph based on their type (label) and/or properties."
    args_schema: type[BaseModel] = FindNodesInput

    def __init__(self, semantic_memory, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_semantic_memory', semantic_memory)

    @property
    def semantic_memory(self):
        return self._semantic_memory

    def _run(self, labels: Optional[List[str]] = None, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Synchronous execution wrapper."""
        return asyncio.run(self._arun(labels, properties))

    async def _arun(self, labels: Optional[List[str]] = None, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Async implementation of the tool."""
        try:
            logger.info(f"Finding nodes with labels: {labels} and properties: {properties}")
            nodes = self.semantic_memory.graph_db.find_nodes(labels=labels, properties=properties)
            result_nodes = [node.model_dump() for node in nodes]
            return {"status": "success", "nodes": result_nodes, "count": len(result_nodes)}
        except Exception as e:
            logger.error(f"Error in find_nodes: {e}")
            return {"status": "error", "error": str(e)}

# ==============================================================================
# Tool 3: Find Callers of a Node
# ==============================================================================

class FindCallersInput(BaseModel):
    """Input schema for finding callers."""
    node_id: str = Field(description="The unique ID of the node (e.g., a function) to find the callers of.")

class FindCallers(BaseTool):
    """
    Given a specific node's ID, finds all nodes that have an edge pointing to it.
    Crucial for understanding how and where a function or class is used.
    """
    name: str = "find_callers"
    description: str = "Given a node's ID, finds all nodes that call it."
    args_schema: type[BaseModel] = FindCallersInput

    def __init__(self, semantic_memory, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_semantic_memory', semantic_memory)

    @property
    def semantic_memory(self):
        return self._semantic_memory

    def _run(self, node_id: str) -> Dict[str, Any]:
        """Synchronous execution wrapper."""
        return asyncio.run(self._arun(node_id))

    async def _arun(self, node_id: str) -> Dict[str, Any]:
        """Async implementation of the tool."""
        try:
            logger.info(f"Finding callers for node: '{node_id}'")
            callers = self.semantic_memory.graph_db.find_callers(node_id)
            return {"status": "success", "node_id": node_id, "callers": callers, "count": len(callers)}
        except Exception as e:
            logger.error(f"Error in find_callers: {e}")
            return {"status": "error", "error": str(e)}

# ==============================================================================
# Tool 4: Find Callees of a Node
# ==============================================================================

class FindCalleesInput(BaseModel):
    """Input schema for finding callees."""
    node_id: str = Field(description="The unique ID of the node to find the callees of.")

class FindCallees(BaseTool):
    """
    Given a specific node's ID, finds all nodes it has an edge pointing to.
    Essential for understanding what other functions a piece of code depends on.
    """
    name: str = "find_callees"
    description: str = "Given a node's ID, finds all nodes that it calls."
    args_schema: type[BaseModel] = FindCalleesInput

    def __init__(self, semantic_memory, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_semantic_memory', semantic_memory)

    @property
    def semantic_memory(self):
        return self._semantic_memory

    def _run(self, node_id: str) -> Dict[str, Any]:
        """Synchronous execution wrapper."""
        return asyncio.run(self._arun(node_id))

    async def _arun(self, node_id: str) -> Dict[str, Any]:
        """Async implementation of the tool."""
        try:
            logger.info(f"Finding callees for node: '{node_id}'")
            callees = self.semantic_memory.graph_db.find_callees(node_id)
            return {"status": "success", "node_id": node_id, "callees": callees, "count": len(callees)}
        except Exception as e:
            logger.error(f"Error in find_callees: {e}")
            return {"status": "error", "error": str(e)}

# ==============================================================================
# Tool 5: Get Entity by ID (Entity Store)
# ==============================================================================

class GetEntityByIdInput(BaseModel):
    """Input schema for getting entities by ID."""
    entity_ids: List[str] = Field(description="A list of unique entity IDs to retrieve.")

class GetEntityById(BaseTool):
    """
    Retrieves the full details for one or more specific entities given their unique IDs.
    """
    name: str = "get_entity_by_id"
    description: str = "Retrieves full details for specific entities given their unique IDs."
    args_schema: type[BaseModel] = GetEntityByIdInput

    def __init__(self, semantic_memory, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_semantic_memory', semantic_memory)

    @property
    def semantic_memory(self):
        return self._semantic_memory

    def _run(self, entity_ids: List[str]) -> Dict[str, Any]:
        """Synchronous execution wrapper."""
        return asyncio.run(self._arun(entity_ids))

    async def _arun(self, entity_ids: List[str]) -> Dict[str, Any]:
        """Async implementation of the tool."""
        try:
            logger.info(f"Looking up details for {len(entity_ids)} entities by ID.")
            entities = [self.semantic_memory.entity_store.get_entity(eid) for eid in entity_ids]
            found_entities = [e.model_dump() for e in entities if e]
            return {"status": "success", "entities": found_entities}
        except Exception as e:
            logger.error(f"Error in get_entity_by_id: {e}")
            return {"status": "error", "error": str(e)}

# ==============================================================================
# Tool 6: Get Entities by Type (Entity Store)
# ==============================================================================

class GetEntitiesByTypeInput(BaseModel):
    """Input schema for getting entities by type."""
    entity_type: str = Field(description="The type of entities to retrieve (e.g., 'function', 'class').")

class GetEntitiesByType(BaseTool):
    """
    Retrieves a list of all entities of a specific type.
    """
    name: str = "get_entities_by_type"
    description: str = "Retrieves all entities of a specific type (e.g., 'function', 'class')."
    args_schema: type[BaseModel] = GetEntitiesByTypeInput

    def __init__(self, semantic_memory, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_semantic_memory', semantic_memory)

    @property
    def semantic_memory(self):
        return self._semantic_memory
    
    def _run(self, entity_type: str) -> Dict[str, Any]:
        """Synchronous execution wrapper."""
        return asyncio.run(self._arun(entity_type))

    async def _arun(self, entity_type: str) -> Dict[str, Any]:
        """Async implementation of the tool."""
        try:
            logger.info(f"Finding all entities of type: '{entity_type}'.")
            entities = self.semantic_memory.entity_store.find_entities_by_type(entity_type)
            found_entities = [e.model_dump() for e in entities if e]
            return {"status": "success", "entities": found_entities, "count": len(found_entities)}
        except Exception as e:
            logger.error(f"Error in get_entities_by_type: {e}")
            return {"status": "error", "error": str(e)}

# ==============================================================================
# Tool 7: Get All Entities (Entity Store)
# ==============================================================================

class GetAllEntities(BaseTool):
    """
    Retrieves a list of ALL entities of all types stored in the memory.
    """
    name: str = "get_all_entities"
    description: str = "Retrieves a list of all entities of all types. Use with caution."
    
    def __init__(self, semantic_memory, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_semantic_memory', semantic_memory)

    @property
    def semantic_memory(self):
        return self._semantic_memory
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """Synchronous execution wrapper."""
        return asyncio.run(self._arun(**kwargs))

    async def _arun(self, **kwargs) -> Dict[str, Any]:
        """Async implementation of the tool."""
        try:
            logger.info("Retrieving all entities from the store.")
            entities = self.semantic_memory.entity_store.get_all_entities()
            found_entities = [e.model_dump() for e in entities if e]
            return {"status": "success", "entities": found_entities, "count": len(found_entities)}
        except Exception as e:
            logger.error(f"Error in get_all_entities: {e}")
            return {"status": "error", "error": str(e)}

