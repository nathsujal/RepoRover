"""
Tools for the Query Planner Agent to interact with semantic memory.
"""
from typing import Any, Dict, List, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class SemanticSearchInput(BaseModel):
    """Input schema for semantic search."""
    query: str = Field(description="The search query to find semantically similar content")
    limit: int = Field(default=10, description="Maximum number of results to return")


class SemanticSearchTool(BaseTool):
    """Tool for performing semantic search on repository content."""
    
    name: str = "semantic_search"
    description: str = (
        "Searches docs and code summaries for concepts semantically similar to the query. "
        "Best for the first step to get a broad overview of relevant entities. "
        "Input should be a search query string."
    )
    args_schema: type[BaseModel] = SemanticSearchInput
    
    def __init__(self, semantic_memory, **kwargs):
        super().__init__(**kwargs)
        # Store semantic_memory in a way that doesn't conflict with Pydantic
        object.__setattr__(self, '_semantic_memory', semantic_memory)
    
    @property
    def semantic_memory(self):
        return self._semantic_memory
    
    async def _arun(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Async implementation of the tool."""
        try:
            logger.info(f"Performing semantic search for: '{query}' (limit: {limit})")
            search_results = await self.semantic_memory.vector_store.similarity_search_with_score(query, k=limit)
            
            formatted_results = []
            for doc, score in search_results:
                formatted_results.append({
                    "content": doc.content,
                    "metadata": doc.metadata if hasattr(doc, 'metadata') else {},
                    "similarity_score": float(score)
                })
            
            logger.info(f"Found {len(formatted_results)} semantic matches")
            return {
                "status": "success",
                "results": formatted_results, 
                "total_found": len(formatted_results)
            }

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return {
                "status": "error",
                "error": str(e),
                "results": [], 
                "total_found": 0
            }
    
    def _run(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Sync implementation - not recommended for async operations."""
        raise NotImplementedError("Use async version (_arun) instead")


class GraphQueryInput(BaseModel):
    """Input schema for graph queries."""
    entity_ids: List[str] = Field(description="List of entity IDs to query relationships for")
    query_type: str = Field(
        default="find_related",
        description="Type of query: 'find_callers', 'find_callees', or 'find_related'"
    )


class GraphQueryTool(BaseTool):
    """Tool for querying the knowledge graph for entity relationships."""
    
    name: str = "graph_query"
    description: str = (
        "Given entity IDs, finds their direct callers, callees, or related entities in the code graph. "
        "Useful for understanding code flow and dependencies. "
        "Query types: 'find_callers', 'find_callees', 'find_related'"
    )
    args_schema: type[BaseModel] = GraphQueryInput
    
    def __init__(self, semantic_memory, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_semantic_memory', semantic_memory)
    
    @property
    def semantic_memory(self):
        return self._semantic_memory
    
    async def _arun(self, entity_ids: List[str], query_type: str = "find_related") -> Dict[str, Any]:
        """Async implementation of the tool."""
        try:
            logger.info(f"Performing graph query: {query_type} for {len(entity_ids)} entities")
            relationships: List[Dict[str, Any]] = []

            for entity_id in entity_ids:
                if query_type == "find_callers":
                    callers = await self._get_callers(entity_id)
                    for caller_id in callers:
                        relationships.append({
                            "type": "calls",
                            "source_id": caller_id,
                            "target_id": entity_id,
                            "relationship": "caller"
                        })
                elif query_type == "find_callees":
                    callees = await self._get_callees(entity_id)
                    for callee_id in callees:
                        relationships.append({
                            "type": "calls",
                            "source_id": entity_id,
                            "target_id": callee_id,
                            "relationship": "callee"
                        })
                else:  # find_related
                    callers = await self._get_callers(entity_id)
                    callees = await self._get_callees(entity_id)
                    for caller_id in callers:
                        relationships.append({
                            "type": "related",
                            "source_id": caller_id,
                            "target_id": entity_id,
                            "relationship": "caller"
                        })
                    for callee_id in callees:
                        relationships.append({
                            "type": "related",
                            "source_id": entity_id,
                            "target_id": callee_id,
                            "relationship": "callee"
                        })

            entity_ids_in_results = {rel.get(k) for rel in relationships for k in ("source_id", "target_id") if rel.get(k)}
            logger.info(f"Found {len(relationships)} relationships involving {len(entity_ids_in_results)} entities")
            
            return {
                "status": "success",
                "relationships": relationships, 
                "entity_count": len(entity_ids_in_results)
            }
                
        except Exception as e:
            logger.error(f"Error in graph query: {e}")
            return {
                "status": "error",
                "error": str(e),
                "relationships": [], 
                "entity_count": 0
            }
    
    async def _get_callers(self, entity_id: str) -> List[str]:
        """Helper to get callers, handling both sync and async graph_db methods."""
        try:
            if hasattr(self.semantic_memory.graph_db, 'find_callers'):
                result = self.semantic_memory.graph_db.find_callers(entity_id)
                # Check if result is awaitable
                if hasattr(result, '__await__'):
                    return await result
                return result if result else []
        except Exception as e:
            logger.warning(f"Error getting callers for {entity_id}: {e}")
        return []
    
    async def _get_callees(self, entity_id: str) -> List[str]:
        """Helper to get callees, handling both sync and async graph_db methods."""
        try:
            if hasattr(self.semantic_memory.graph_db, 'find_callees'):
                result = self.semantic_memory.graph_db.find_callees(entity_id)
                # Check if result is awaitable
                if hasattr(result, '__await__'):
                    return await result
                return result if result else []
        except Exception as e:
            logger.warning(f"Error getting callees for {entity_id}: {e}")
        return []
    
    def _run(self, entity_ids: List[str], query_type: str = "find_related") -> Dict[str, Any]:
        """Sync implementation - not recommended for async operations."""
        raise NotImplementedError("Use async version (_arun) instead")


class EntityLookupInput(BaseModel):
    """Input schema for entity lookup."""
    entity_ids: List[str] = Field(description="List of entity IDs to retrieve detailed information for")


class EntityLookupTool(BaseTool):
    """Tool for looking up detailed entity information."""
    
    name: str = "entity_lookup"
    description: str = (
        "Given a list of entity IDs, retrieves their full details including raw source code. "
        "Use this when you need the full implementation details of specific code entities."
    )
    args_schema: type[BaseModel] = EntityLookupInput
    
    def __init__(self, semantic_memory, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_semantic_memory', semantic_memory)
    
    @property
    def semantic_memory(self):
        return self._semantic_memory
    
    async def _arun(self, entity_ids: List[str]) -> Dict[str, Any]:
        """Async implementation of the tool."""
        try:
            logger.info(f"Looking up details for {len(entity_ids)} entities")
            entities: List[Dict[str, Any]] = []
            
            for entity_id in entity_ids:
                entity = await self._get_entity(entity_id)
                if entity:
                    # Convert to dict if it's a Pydantic model
                    if hasattr(entity, 'model_dump'):
                        entities.append(entity.model_dump())
                    elif hasattr(entity, 'dict'):
                        entities.append(entity.dict())
                    elif isinstance(entity, dict):
                        entities.append(entity)
                    else:
                        # Fallback for other types
                        entities.append({"id": entity_id, "data": str(entity)})
                else:
                    logger.warning(f"Entity not found: {entity_id}")
            
            logger.info(f"Successfully retrieved {len(entities)} entity details")
            return {
                "status": "success",
                "entities": entities, 
                "found_count": len(entities),
                "requested_count": len(entity_ids)
            }
            
        except Exception as e:
            logger.error(f"Error in entity lookup: {e}")
            return {
                "status": "error",
                "error": str(e),
                "entities": [], 
                "found_count": 0,
                "requested_count": len(entity_ids)
            }
    
    async def _get_entity(self, entity_id: str) -> Optional[Any]:
        """Helper to get entity, handling both sync and async entity_store methods."""
        try:
            if hasattr(self.semantic_memory.entity_store, 'get_entity'):
                result = self.semantic_memory.entity_store.get_entity(entity_id)
                # Check if result is awaitable
                if hasattr(result, '__await__'):
                    return await result
                return result
        except Exception as e:
            logger.warning(f"Error getting entity {entity_id}: {e}")
        return None
    
    def _run(self, entity_ids: List[str]) -> Dict[str, Any]:
        """Sync implementation - not recommended for async operations."""
        raise NotImplementedError("Use async version (_arun) instead")


class CodeSearchInput(BaseModel):
    """Input schema for code search."""
    query: str = Field(description="Search query for code patterns or specific implementations")
    file_type: Optional[str] = Field(default=None, description="Optional file type filter (e.g., '.py', '.js')")
    limit: int = Field(default=5, description="Maximum number of results to return")


class CodeSearchTool(BaseTool):
    """Tool for searching specific code patterns or implementations."""
    
    name: str = "code_search"
    description: str = (
        "Searches for specific code patterns, function names, or implementations. "
        "More targeted than semantic search for finding exact matches or similar code structures."
    )
    args_schema: type[BaseModel] = CodeSearchInput
    
    def __init__(self, semantic_memory, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_semantic_memory', semantic_memory)
    
    @property
    def semantic_memory(self):
        return self._semantic_memory
    
    async def _arun(self, query: str, file_type: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
        """Async implementation of the tool."""
        try:
            logger.info(f"Performing code search for: '{query}' (file_type: {file_type}, limit: {limit})")
            
            # Create filter for file type if specified
            filters = {}
            if file_type:
                filters["file_extension"] = file_type
            
            # Perform search with filters if the vector store supports it
            try:
                if filters:
                    search_results = await self.semantic_memory.vector_store.similarity_search_with_score(
                        query, k=limit, filter=filters
                    )
                else:
                    search_results = await self.semantic_memory.vector_store.similarity_search_with_score(
                        query, k=limit
                    )
            except TypeError:
                # Fallback if filter parameter is not supported
                search_results = await self.semantic_memory.vector_store.similarity_search_with_score(
                    query, k=limit
                )
            
            formatted_results = []
            for doc, score in search_results:
                content = doc.page_content if hasattr(doc, 'page_content') else doc.content
                metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                
                # Apply file type filtering manually if needed
                if file_type:
                    file_path = metadata.get("file_path", "")
                    if not file_path.endswith(file_type):
                        continue
                
                # Only include code-related results
                if any(keyword in content.lower() for keyword in ['def ', 'function', 'class ', 'import ', 'from ', '{', '}', '(']):
                    formatted_results.append({
                        "content": content,
                        "metadata": metadata,
                        "similarity_score": float(score),
                        "file_path": metadata.get("file_path", "unknown"),
                        "entity_type": metadata.get("entity_type", "code")
                    })
            
            logger.info(f"Found {len(formatted_results)} code matches")
            return {
                "status": "success",
                "results": formatted_results,
                "total_found": len(formatted_results)
            }

        except Exception as e:
            logger.error(f"Error in code search: {e}")
            return {
                "status": "error",
                "error": str(e),
                "results": [],
                "total_found": 0
            }
    
    def _run(self, query: str, file_type: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
        """Sync implementation - not recommended for async operations."""
        raise NotImplementedError("Use async version (_arun) instead")


# Factory function to create tools (alternative approach)
def create_query_planner_tools(semantic_memory) -> List[BaseTool]:
    """Factory function to create all query planner tools."""
    return [
        SemanticSearchTool(semantic_memory),
        GraphQueryTool(semantic_memory),
        EntityLookupTool(semantic_memory),
        CodeSearchTool(semantic_memory),
    ]