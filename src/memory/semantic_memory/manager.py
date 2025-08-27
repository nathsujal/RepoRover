from typing import Dict, List, Any, Optional

from src.memory.semantic_memory.vector_store.config import VectorStoreConfig
from .graph_db import NetworkXGraphDatabase, Node, Relationship
from .vector_store import ChromaVectorStore, VectorDocument
from .entity_store import SQLiteEntityStore, Entity

import logging
logger = logging.getLogger(__name__)

class SemanticMemoryManager:
    def __init__(self):
        """Initialize all the underlying memory components."""
        self.graph_db = NetworkXGraphDatabase()
        vector_store_config = VectorStoreConfig()
        self.vector_store = ChromaVectorStore(config=vector_store_config)
        self.entity_store = SQLiteEntityStore(db_path="semantic_entities.db")
        
        logger.info("Semantic Memory Manager initiated successfully.")

    async def add_entity(
        self,
        unique_id: str,
        type: str,
        content: str,
        properties: Dict[str, Any],
        embedding: List[float]
    ) -> bool:
        """Adds a new entity (like a function or doc chunk) to all memory stores.
        This is the primary method for populating the semantic memory.

        Args:
            unique_id: A unique identifier (e.g., 'function:utils.py:process_data').
            content: The raw text content of the entity.
            properties: A dictionary of structured metadata.
            embedding: The pre-computed vector embedding of the content.

        Returns:
            True if the entity was added successfully to all stores.
        """
        try:
            # Add to Graph DB
            graph_node = Node(id=unique_id, type=type, properties=properties)
            self.graph_db.create_node(graph_node)

            # Add to Vector Store
            vector_doc = VectorDocument(
                id=unique_id,
                content=content or '',
                embedding=embedding,
                metadata={'type': type, **properties}
            )
            await self.vector_store.add_documents([vector_doc])
                
            # Add to Entity Store
            entity = Entity(
                unique_id=unique_id,
                type=type,
                summary=properties.get('summary', ''),
                details=content,
                code=properties.get('code', ''),
                source=properties.get('file_path', '')
            )
            self.entity_store.add_entity(entity)

            logger.debug(f"Successfully added entity '{unique_id}' to all memory stores.")
            return True
        except Exception as e:
            logger.error(f"Failed to add entity '{unique_id}': {e}")
            return False

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """Adds a directional relationship between two entities in the graph."""
        rel = Relationship(
            source_id=source_id,
            target_id=target_id,
            type=relationship_type,
            properties=properties or {}
        )
        self.graph_db.create_relationship(rel)
        logger.debug(f"Added relationship: ({source_id})-[{relationship_type}]->({target_id})")

    async def hybrid_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a hybrid search, enriching semantic results with structural context.

        Args:
            query: The natural language query.
            k: The number of initial semantic results to fetch.

        Returns:
            A list of dictionaries, each representing an enriched entity.
        """
        logger.info(f"Performing hybrid search for query: '{query}'")
        
        # 1. Semantic Search: Find initial candidates from the vector store
        semantic_results = await self.vector_store.similarity_search(query=query, k=k)
        if not semantic_results:
            logger.warning("Semantic search returned no results.")
            return []

        # 2. Contextual Enrichment: Use the graph and entity stores
        enriched_context = []
        all_related_ids = {doc.id for doc in semantic_results}

        for doc in semantic_results:
            # Find related nodes in the graph
            node_id = doc.id
            callers = self.graph_db.find_callers(node_id)
            callees = self.graph_db.find_callees(node_id)
            all_related_ids.update(callers)
            all_related_ids.update(callees)

        # 3. Final Retrieval: Get the full details for all unique IDs
        for entity_id in all_related_ids:
            entity_details = self.entity_store.get_entity(entity_id)
            if entity_details:
                enriched_context.append(entity_details.model_dump())
        
        logger.info(f"Hybrid search completed. Found {len(enriched_context)} enriched context items.")
        return enriched_context

    async def clear_all(self) -> None:
        """Clears all underlying memory stores to prepare for a new ingestion."""
        self.graph_db.clear()
        self.entity_store.clear()
        await self.vector_store.clear()
        logger.info("All semantic memory stores have been cleared.")