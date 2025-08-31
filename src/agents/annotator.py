"""
Annotator Agent: Enriches code entities with natural language summaries.
"""
import logging
import asyncio
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor
import gc
import torch

from pydantic import BaseModel

from src.models.geminiModel import GeminiModel
from src.memory.semantic_memory.manager import SemanticMemoryManager
from src.memory.core_memory import CoreMemory
from src.memory.episodic_memory.manager import EpisodicMemoryManager

logger = logging.getLogger(__name__)

class AnnotatorConfig(BaseModel):
    """Configuration for the Annotator agent."""
    agent_name: str = "annotator"
    description: str = "Generates summaries for code blocks and adds embeddings."
    model_name: str = "gemma-3-4b-it"
    batch_size: int = 3
    memory_cleanup_interval: int = 5

class AnnotatorAgent():
    """
    The Annotator agent enriches code entities with natural language summaries.
    Optimized for resource-constrained environments like Mac Mini.
    """

    def __init__(self, semantic_memory: SemanticMemoryManager, core_memory: CoreMemory, episodic_memory: EpisodicMemoryManager):
        self.config = AnnotatorConfig()
        self.name = self.config.agent_name
        self.description = self.config.description
        self.model = GeminiModel()
        self.semantic_memory = semantic_memory
        self.core_memory = core_memory
        self.episodic_memory = episodic_memory
        self._thread_executor = ThreadPoolExecutor(max_workers=1)  # Single thread for Mac

    def _create_summary_prompt(self, code_snippet: str, entity_name: str = "") -> str:
        """Create a prompt for code summarization."""
        entity_context = f" named '{entity_name}'" if entity_name else ""
        return (
            f"Provide a single, concise sentence that describes the purpose of the following Python function{entity_context}. "
            "Do not add any introductory phrases or explanatory text. Just provide the summary.\n\n"
            f"```python\n{code_snippet}\n```\n\n"
            "Summary:"
        )

    def _extract_code_from_entity(self, entity) -> tuple[str, str]:
        """Extract code and entity name from entity object."""
        try:
            code = entity.type
            entity_name = entity.unique_id

            return code, entity_name
            
        except Exception as e:
            logger.error(f"Error extracting code from entity: {str(e)}")
            return "", ""

    def _clean_summary(self, summary: str) -> str:
        """Clean up generated summary."""
        if not isinstance(summary, str):
            return "Function summary unavailable."
        
        summary = summary.strip()
        
        # Remove common prefixes that models might add
        prefixes_to_remove = [
            "Summary:", "This function", "The function", 
            "This code", "The code", "Purpose:", "Description:"
        ]
        
        for prefix in prefixes_to_remove:
            if summary.lower().startswith(prefix.lower()):
                summary = summary[len(prefix):].strip()
                break
        
        # Remove any leading colons, dashes, or quotes
        summary = summary.lstrip(":-\"'").strip()
        
        return summary if summary else "Function purpose not determined."

    async def _generate_single_summary(self, entity) -> tuple:
        """Generate summary for a single entity with proper error handling."""
        try:
            # Extract code and entity name
            code_snippet = getattr(entity, 'code', '')
            entity_name = getattr(entity, 'type', '')
            entity_id = getattr(entity, 'unique_id', 'unknown')

            if code_snippet == '':
                logger.warning(f"Entity {entity_id} has no code details")
                return entity, "No code details available.", None
            
            logger.debug(f"Processing entity {entity_id} ({entity_name})")
            logger.debug(f"Code snippet length: {len(code_snippet)} chars")
            logger.debug(f"Code preview: {code_snippet[:100]}...")
            
            prompt = self._create_summary_prompt(code_snippet, entity_name)
            
            logger.debug(f"Generating summary for entity {entity_id}")
            
            raw_summary = self.model.generate(prompt)
            
            summary = self._clean_summary(raw_summary)
            logger.debug(f"Generated summary for {entity_id}: {summary[:50]}...")
            
            return entity, summary, None
            
        except Exception as e:
            logger.error(f"Error generating summary for entity {getattr(entity, 'unique_id', 'unknown')}: {str(e)}")
            return entity, "Function summary unavailable due to generation error.", str(e)

    async def _generate_embeddings_batch(self, summaries: List[str]) -> List:
        """Generate embeddings for a batch of summaries."""
        try:
            embedding_function = self.semantic_memory.vector_store._embedding_function
            embeddings = embedding_function(summaries)
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return [None] * len(summaries)

    def _cleanup_memory(self):
        """Clean up memory to prevent issues on Mac Mini."""
        try:
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
            gc.collect()
            logger.debug("Memory cleanup completed")
        except Exception as e:
            logger.warning(f"Memory cleanup failed: {str(e)}")

    async def _update_entity_and_vector_store(self, entity, summary: str, embedding) -> bool:
        """Update entity and vector store with summary and embedding."""
        try:
            # Update entity with summary
            entity.summary = summary
            
            # Also store summary in properties for consistency
            if hasattr(entity, 'properties') and entity.properties:
                entity.properties['summary'] = summary
            
            self.semantic_memory.entity_store.add_entity(entity)
            logger.debug(f"Updated entity {getattr(entity, 'unique_id', 'unknown')} with summary")
            
            # Update vector store if embedding is available
            if embedding is not None:
                try:
                    entity_id = getattr(entity, 'unique_id', None)
                    if entity_id:
                        vector_doc = await self.semantic_memory.vector_store.retrieve(entity_id)
                        if vector_doc:
                            vector_doc.embedding = embedding
                            vector_doc.content = summary
                            await self.semantic_memory.vector_store.add_documents([vector_doc])
                            logger.debug(f"Updated vector store for {entity_id}")
                except Exception as e:
                    logger.warning(f"Failed to update vector store for {getattr(entity, 'unique_id', 'unknown')}: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating entity {getattr(entity, 'unique_id', 'unknown')}: {str(e)}")
            return False

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the code annotation process with Mac Mini optimizations.
        """
        logger.info("Annotator Agent: Starting code annotation process (Mac Mini optimized)")
        self.episodic_memory.add_interaction(
            agent_name=self.name,
            interaction_type="internal_thought",
            content="Starting code annotation process.",
            interaction_metadata={}
        )
        
        try:
            # Verify model is loaded
            if self.model is None:
                logger.error("Model not initialized. Cannot proceed with annotation.")
                return {
                    "status": "error", 
                    "message": "Model not properly initialized"
                }
            
            # Get function entities to annotate
            function_entities = self.semantic_memory.entity_store.find_entities_by_type("function")
            if not function_entities:
                logger.warning("No function entities found to annotate")
                return {
                    "status": "success", 
                    "message": "No functions to annotate"
                }

            logger.info(f"Found {len(function_entities)} functions to annotate")
            self.episodic_memory.add_interaction(
                agent_name=self.name,
                interaction_type="internal_thought",
                content=f"Found {len(function_entities)} functions to annotate.",
                interaction_metadata={"function_count": len(function_entities)}
            )
            
            total_successful = 0
            total_entities = len(function_entities)
            batch_size = self.config.batch_size
            
            # Process entities in small batches
            for i in range(0, total_entities, batch_size):
                batch = function_entities[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (total_entities + batch_size - 1) // batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} entities)")
                
                # Generate summaries sequentially to avoid overwhelming Mac Mini
                summaries = []
                entities_batch = []
                errors = []
                
                for entity in batch:
                    entity_result, summary, error = await self._generate_single_summary(entity)
                    entities_batch.append(entity_result)
                    summaries.append(summary)
                    errors.append(error)
                    
                    # Small delay to prevent overwhelming the system
                    await asyncio.sleep(0.1)
                
                # Generate embeddings for the batch
                embeddings = await self._generate_embeddings_batch(summaries)
                
                # Update entities and vector store
                batch_successful = 0
                for j, (entity, summary, error) in enumerate(zip(entities_batch, summaries, errors)):
                    if error is None:  # Only update if generation was successful
                        embedding = embeddings[j] if j < len(embeddings) else None
                        if await self._update_entity_and_vector_store(entity, summary, embedding):
                            batch_successful += 1
                
                total_successful += batch_successful
                
                logger.info(f"Batch {batch_num} complete: {batch_successful}/{len(batch)} successful")
                
                # Clean up memory every few entities (Mac Mini optimization)
                if batch_num % self.config.memory_cleanup_interval == 0:
                    self._cleanup_memory()
                
                # Longer delay between batches for Mac Mini
                if batch_num < total_batches:
                    await asyncio.sleep(1.0)
            
            success_rate = (total_successful / total_entities) * 100 if total_entities > 0 else 0
            
            logger.info(f"Annotation process complete: {total_successful}/{total_entities} functions ({success_rate:.1f}% success rate)")
            
            self.episodic_memory.add_interaction(
                agent_name=self.name,
                interaction_type="internal_action",
                content=f"Annotation process complete. Successfully annotated {total_successful}/{total_entities} functions.",
                interaction_metadata={
                    "total_functions": total_entities,
                    "successful_annotations": total_successful,
                    "success_rate": success_rate
                }
            )
            
            return {
                "status": "success",
                "message": f"Successfully annotated {total_successful}/{total_entities} functions ({success_rate:.1f}% success rate)",
                "total_functions": total_entities,
                "successful_annotations": total_successful,
                "success_rate": success_rate
            }
            
        except Exception as e:
            logger.exception("Critical error in annotation process")
            return {
                "status": "error",
                "message": f"Annotation process failed: {str(e)}"
            }
    
    def __del__(self):
        """Cleanup thread executor when agent is destroyed."""
        try:
            if hasattr(self, '_thread_executor'):
                self._thread_executor.shutdown(wait=True)
        except Exception:
            pass