"""
Librarian Agent: Processes documentation files and populates semantic memory.
"""
import logging
from typing import List, Type, Dict, Any

from pydantic import BaseModel

from src.memory.semantic_memory.manager import SemanticMemoryManager
from src.memory.core_memory import CoreMemory
from src.memory.episodic_memory.manager import EpisodicMemoryManager
from src.tools.text_chunker import chunk_text

logger = logging.getLogger(__name__)

async def run_librarian_agent(
    doc_file_paths: List[str],
    semantic_memory: SemanticMemoryManager,
    episodic_memory: EpisodicMemoryManager,
    agent_name: str
):
    """
    Orchestrates the processing of documentation files.

    Args:
        doc_file_paths: A list of paths to documentation files.
        semantic_memory: An instance of the SemanticMemoryManager.
    """
    logger.info(f"Librarian Agent: Starting analysis on {len(doc_file_paths)} doc files.")
    episodic_memory.add_interaction(
        agent_name=agent_name,
        interaction_type="internal_thought",
        content=f"Starting analysis of {len(doc_file_paths)} documentation files.",
        interaction_metadata={"file_count": len(doc_file_paths)}
    )

    all_chunks = []
    chunk_metadatas = []
    total_chars_processed = 0

    # --- 1. Read and Chunk all documents ---
    for file_path in doc_file_paths:
        try:
            logger.debug(f"Reading file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                logger.warning(f"File {file_path} is empty, skipping.")
                continue
            
            total_chars_processed += len(content)
            logger.debug(f"File {file_path} contains {len(content)} characters")
            
            chunks = chunk_text(content)
            logger.debug(f"Split {file_path} into {len(chunks)} chunks")
            
            all_chunks.extend(chunks)
            
            # Create metadata for each chunk to track its origin
            for i, chunk in enumerate(chunks):
                chunk_metadatas.append({
                    "source_file": file_path,
                    "chunk_number": i,
                    "total_chunks": len(chunks),
                    "chunk_size": len(chunk),
                    "file_type": "documentation"
                })
                
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error reading {file_path}: {e}")
            try:
                # Try with different encoding
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                chunks = chunk_text(content)
                all_chunks.extend(chunks)
                for i, chunk in enumerate(chunks):
                    chunk_metadatas.append({
                        "source_file": file_path,
                        "chunk_number": i,
                        "total_chunks": len(chunks),
                        "chunk_size": len(chunk),
                        "file_type": "documentation",
                        "encoding": "latin-1"
                    })
                logger.info(f"Successfully read {file_path} with latin-1 encoding")
            except Exception as fallback_error:
                logger.error(f"Failed to read file {file_path} even with fallback encoding: {fallback_error}")
                
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Failed to read or chunk file {file_path}: {e}")

    if not all_chunks:
        logger.warning("No text chunks were created from the documentation.")
        return {
            "status": "warning",
            "message": "No text chunks were created from documentation files."
        }

    logger.info(f"Created {len(all_chunks)} chunks from {total_chars_processed} characters across {len(doc_file_paths)} files")
    episodic_memory.add_interaction(
        agent_name=agent_name,
        interaction_type="internal_action",
        content=f"Read and chunked {len(doc_file_paths)} files, creating {len(all_chunks)} chunks.",
        interaction_metadata={"files_processed": len(doc_file_paths), "chunks_created": len(all_chunks)}
    )

    # --- 2. Generate Embeddings in a Batch ---
    try:
        logger.info(f"Generating embeddings for {len(all_chunks)} text chunks...")
        embedding_function = semantic_memory.vector_store.embedding_function
        
        if not embedding_function:
            logger.error("No embedding function available in vector store")
            return {
                "status": "error",
                "message": "No embedding function available"
            }
        
        embeddings = embedding_function(all_chunks)
        logger.info(f"Successfully generated {len(embeddings)} embeddings")
        
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        # Continue without embeddings
        embeddings = [None] * len(all_chunks)

    # --- 3. Populate Semantic Memory ---
    logger.info("Populating semantic memory with document chunks...")
    successful_entities = 0
    
    for i, chunk in enumerate(all_chunks):
        try:
            unique_id = f"document:{chunk_metadatas[i]['source_file']}:chunk_{chunk_metadatas[i]['chunk_number']}"
            
            # Enhanced properties for better tracking
            properties = {
                **chunk_metadatas[i],
                'content_preview': chunk[:100] + "..." if len(chunk) > 100 else chunk,
                'entity_type': 'document_chunk'
            }
            
            await semantic_memory.add_entity(
                unique_id=unique_id,
                type="document_chunk",
                content=chunk,
                properties=properties,
                embedding=embeddings[i] if i < len(embeddings) else None
            )
            successful_entities += 1
            
        except Exception as e:
            logger.error(f"Failed to add entity for chunk {i}: {e}")
    
    logger.info(f"Librarian Agent: Successfully created {successful_entities}/{len(all_chunks)} document entities")
    episodic_memory.add_interaction(
        agent_name=agent_name,
        interaction_type="internal_action",
        content=f"Populated semantic memory with {successful_entities} document chunk entities.",
        interaction_metadata={"entities_created": successful_entities}
    )
    
    return {
        "status": "success",
        "message": f"Processed {len(doc_file_paths)} files, created {successful_entities} document entities",
        "files_processed": len(doc_file_paths),
        "chunks_created": len(all_chunks),
        "entities_created": successful_entities,
        "total_characters": total_chars_processed
    }

class LibrarianConfig(BaseModel):
    """Configuration for the Librarian agent."""
    agent_name: str = "librarian"
    description: str = "Processes documentation files and populates semantic memory."
    model_name: str = "N/A"
    model_class: Type = None

class LibrarianAgent():
    """
    The Librarian agent is a wrapper for the core logic that processes documentation files.
    """
    def __init__(self, semantic_memory: SemanticMemoryManager, core_memory: CoreMemory, episodic_memory: EpisodicMemoryManager):
        config = LibrarianConfig()
        self.config = config
        self.name = config.agent_name
        self.description = config.description
        self.semantic_memory = semantic_memory
        self.core_memory = core_memory
        self.episodic_memory = episodic_memory
        self.model = None
        logger.info(f"{self.name} agent initialized without an LLM.")

    @classmethod
    def get_config_class(cls):
        """Get the configuration class for this agent."""
        return LibrarianConfig

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        doc_file_paths = input_data.get("doc_file_paths")
        if not doc_file_paths:
            logger.error("No doc file paths provided to Librarian Agent")
            return {"status": "error", "message": "No doc file paths provided."}
        
        logger.info(f"Librarian Agent executing on {len(doc_file_paths)} files")
        
        try:
            result = await run_librarian_agent(
                doc_file_paths=doc_file_paths,
                semantic_memory=self.semantic_memory,
                episodic_memory=self.episodic_memory,
                agent_name=self.name
            )
            
            if isinstance(result, dict):
                return result
            else:
                # If run_librarian_agent doesn't return a dict, create a success response
                return {
                    "status": "success",
                    "message": f"Processed {len(doc_file_paths)} documentation files and populated semantic memory."
                }
                
        except Exception as e:
            logger.exception("Error in Librarian Agent execution")
            return {
                "status": "error",
                "message": f"Failed to process documentation files: {str(e)}"
            }