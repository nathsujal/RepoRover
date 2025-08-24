"""
Architect Agent: Parses source code to build a structural map of the repository.
"""
import logging
from typing import Any, Dict, List, Type

from .base import AgentConfig, BaseAgent
from src.tools.code_parser import parse_python_file, CodeVisitor
from src.memory.semantic_memory.manager import SemanticMemoryManager

logger = logging.getLogger(__name__)


def _sanitize_metadata(properties: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitizes metadata to ensure compatibility with ChromaDB."""
    sanitized = {}
    for key, value in properties.items():
        if isinstance(value, list):
            sanitized[key] = ", ".join(map(str, value))
        else:
            sanitized[key] = value
    return sanitized


# --- Agent Core Logic ---

async def run_architect_agent(
    file_paths: List[str],
    semantic_memory: SemanticMemoryManager
):
    """
    Orchestrates the analysis of source code files to populate the semantic memory.
    """
    logger.info(f"Architect Agent: Starting analysis on {len(file_paths)} files.")

    all_visitors: List[CodeVisitor] = []
    file_nodes: Dict[str, str] = {}

    # --- PASS 1: Discover and Store All Code Entities (Nodes) ---
    for file_path in file_paths:
        logger.debug(f"Architect: Parsing {file_path}")
        visitor = parse_python_file(file_path)
        if not visitor:
            logger.warning(f"Failed to parse {file_path}")
            continue
        
        all_visitors.append(visitor)

        # Create a node for the file itself
        file_node_id = f"file:{file_path}"
        file_nodes[file_path] = file_node_id
        await semantic_memory.add_entity(
            unique_id=file_node_id,
            type='file',
            content="",
            properties={"path": file_path},
            embedding=None
        )

        # Add function nodes to memory with proper code storage
        for func_name, properties in visitor.functions.items():
            unique_id = f"function:{file_path}:{func_name}"
            docstring = properties.get('docstring') or ''
            
            # Extract the actual function code - now correctly reading from 'content' field
            func_code = properties['content']
            
            # Log the extracted function code details
            logger.debug(f"Adding function entity: {unique_id}")
            logger.debug(f"Function code length: {len(func_code)} chars")
            
            if not func_code:
                logger.warning(f"No code content found for function {func_name} in {file_path}")
            else:
                logger.debug(f"Function code preview: {func_code[:100]}...")
            
            # Enhanced properties with all necessary information
            enhanced_properties = {
                **properties,
                'file_path': file_path,
                'function_name': func_name,
                'details': func_code,  # Store code as 'details' for annotator
                'code': func_code,     # Also keep as 'code' for consistency
                'source_code': func_code,  # Additional alias for compatibility
            }
            
            await semantic_memory.add_entity(
                unique_id=unique_id,
                type='function',
                content=docstring,
                properties=_sanitize_metadata(enhanced_properties),
                embedding=None
            )

        # Add class nodes to memory
        for class_name, properties in visitor.classes.items():
            unique_id = f"class:{file_path}:{class_name}"
            
            # Extract class code - now correctly reading from 'content' field
            class_code = properties.get('content', '')
            
            logger.debug(f"Adding class entity: {unique_id}")
            logger.debug(f"Class code length: {len(class_code)} chars")
            
            if not class_code:
                logger.warning(f"No code content found for class {class_name} in {file_path}")
            else:
                logger.debug(f"Class code preview: {class_code[:100]}...")
            
            enhanced_properties = {
                **properties,
                'file_path': file_path,
                'class_name': class_name,
                'details': class_code,
                'code': class_code,
                'source_code': class_code,
            }
            
            await semantic_memory.add_entity(
                unique_id=unique_id,
                type='class',
                content="",
                properties=_sanitize_metadata(enhanced_properties),
                embedding=None
            )

    logger.info(f"Architect Agent: Created entities from {len(all_visitors)} files.")

    # --- PASS 2: Create Relationships Between Entities (Edges) ---
    logger.info("Architect Agent: Creating relationships between entities.")
    relationships_created = 0
    
    for visitor in all_visitors:
        file_path = visitor.file_path
        source_file_id = file_nodes.get(file_path)
        
        if not source_file_id:
            logger.warning(f"No file node found for {file_path}")
            continue

        # Create 'DEFINED_IN' relationships for functions and classes
        for func_name in visitor.functions:
            target_id = f"function:{file_path}:{func_name}"
            semantic_memory.add_relationship(source_file_id, target_id, "DEFINED_IN")
            relationships_created += 1
        
        for class_name in visitor.classes:
            target_id = f"class:{file_path}:{class_name}"
            semantic_memory.add_relationship(source_file_id, target_id, "DEFINED_IN")
            relationships_created += 1

        # Create 'IMPORTS' relationships
        for alias, module_path in visitor.imports.items():
            # This is a simplified relationship. A more advanced version would
            # resolve the exact file path for the imported module.
            target_id = f"module:{module_path}"
            semantic_memory.add_relationship(source_file_id, target_id, "IMPORTS")
            relationships_created += 1

        # Create 'CONTAINS_METHOD' relationships
        for class_name, method_name in visitor.class_methods:
            source_id = f"class:{file_path}:{class_name}"
            target_id = f"function:{file_path}:{method_name}"
            semantic_memory.add_relationship(source_id, target_id, "CONTAINS_METHOD")
            relationships_created += 1

        # Create 'CALLS' relationships
        for caller, callee in visitor.calls:
            source_id = f"function:{file_path}:{caller}"
            target_id = f"function:{file_path}:{callee}"
            semantic_memory.add_relationship(source_id, target_id, "CALLS")
            relationships_created += 1

        # Create 'INHERITS_FROM' relationships
        for child, parent in visitor.inheritance:
            source_id = f"class:{file_path}:{child}"
            target_id = f"class:{file_path}:{parent}"
            semantic_memory.add_relationship(source_id, target_id, "INHERITS_FROM")
            relationships_created += 1

    logger.info(f"Architect Agent: Created {relationships_created} relationships.")
    logger.info("Architect Agent: Analysis complete.")


# --- Agent Class Wrapper ---

class ArchitectConfig(AgentConfig):
    """Configuration for the Architect agent."""
    model_name: str = "N/A"
    model_class: Type = None
    temperature: float = 0.0

class ArchitectAgent(BaseAgent):
    """
    The Architect agent is a wrapper for the core logic that parses code
    and populates the Semantic Memory.
    """

    def __init__(self, semantic_memory: SemanticMemoryManager):
        config = ArchitectConfig(
            agent_name="architect",
            description="Parses source code and builds the structural knowledge graph."
        )
        self.config = config
        self.name = config.agent_name
        self.description = config.description
        self.semantic_memory = semantic_memory
        self.model = None # Explicitly setting model to None
        logger.info(f"{self.name} agent initialized without an LLM.")

    @classmethod
    def get_config_class(cls) -> Type[AgentConfig]:
        """Get the configuration class for this agent."""
        return ArchitectConfig

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        file_paths = input_data.get("file_paths")
        if not file_paths:
            logger.error("No file paths provided to Architect Agent")
            return {"status": "error", "message": "No file paths provided."}
        
        logger.info(f"Architect Agent executing on {len(file_paths)} files")
        
        try:
            await run_architect_agent(
                file_paths=file_paths,
                semantic_memory=self.semantic_memory
            )
            
            # Verify entities were created and log some statistics
            function_entities = self.semantic_memory.entity_store.find_entities_by_type("function")
            class_entities = self.semantic_memory.entity_store.find_entities_by_type("class")
            
            logger.info(f"Architect Agent: Created {len(function_entities)} function entities")
            logger.info(f"Architect Agent: Created {len(class_entities)} class entities")
            
            return {
                "status": "success",
                "message": f"Analyzed {len(file_paths)} files and populated semantic memory with {len(function_entities)} functions and {len(class_entities)} classes."
            }
        except Exception as e:
            logger.exception(f"Error in Architect Agent execution")
            return {
                "status": "error",
                "message": f"Failed to analyze files: {str(e)}"
            }