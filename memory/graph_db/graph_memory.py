from neo4j import GraphDatabase
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

from .builder import RepoGraphBuilder
from .querier import RepoGraphQuerier
from .utils import scan_repository, get_source_files, parse_file

logger = logging.getLogger(__name__)

class Neo4jConnection:
    def __init__(self,
                 uri: str = "bolt://localhost:7687",
                 user: str = "neo4j",
                 password: str = "password"):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Connected to Neo4j database successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j database: {e}")
            raise e
        
    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed.")
        
    def execute_query(self, query, parameters=None):
        """Execute a Cypher query and return results"""
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise
            
    def execute_write(self, query, parameters=None):
        """Execute a write query (CREATE, UPDATE, DELETE)"""
        try:
            with self.driver.session() as session:
                result = session.execute_write(self._write_tx, query, parameters or {})
                return result
        except Exception as e:
            logger.error(f"Write query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise
    
    @staticmethod
    def _write_tx(tx, query, parameters):
        result = tx.run(query, parameters)
        return [record.data() for record in result]
    
class Neo4jGraphMemory:
    """Neo4j implementation for RepoRover's graph memory"""
    
    def __init__(self, uri: str = "neo4j://127.0.0.1:7687", user: str = "neo4j", password: str = "password"):
        try:
            self.connection = Neo4jConnection(uri, user, password)
            self.builder = RepoGraphBuilder(self.connection)
            self.querier = RepoGraphQuerier(self.connection)
            self.setup_indexes()
            logger.info("Neo4j Graph Memory initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j Graph Memory: {e}")
            # Could implement fallback to mock here
            raise

    def setup_indexes(self):
        """Create necessary indexes for performance"""
        indexes = [
            "CREATE INDEX file_path_index IF NOT EXISTS FOR (f:File) ON (f.path)",
            "CREATE INDEX function_name_index IF NOT EXISTS FOR (func:Function) ON (func.name)",
            "CREATE INDEX class_name_index IF NOT EXISTS FOR (c:Class) ON (c.name)",
            "CREATE INDEX function_file_index IF NOT EXISTS FOR (func:Function) ON (func.name, func.file_path)"
        ]
        
        for index_query in indexes:
            try:
                self.connection.execute_write(index_query)
                logger.debug(f"Created index: {index_query}")
            except Exception as e:
                logger.warning(f"Failed to create index {index_query}: {e}")

    def build_repository_graph(self, repo_path: str):
        """Main function to build the knowledge graph from repository"""
        logger.info(f"Building repository graph for: {repo_path}")
        
        try:
            # Clear existing graph for this repository
            self._clear_repository_graph()
            
            # 1. Create file nodes
            files = scan_repository(repo_path)
            logger.info(f"Found {len(files)} files")
            
            for file_info in files:
                file_id = self.builder.create_file_node(
                    file_info["path"],
                    file_info["language"],
                    file_info["metadata"]
                )
            
            # 2. Parse code and create structure nodes
            source_files = get_source_files(repo_path)
            logger.info(f"Parsing {len(source_files)} source files")
            
            for file_path in source_files:
                parsed = parse_file(file_path)
                
                # Create function nodes and relationships
                for func in parsed.functions:
                    func_id = self.builder.create_function_node(
                        func.name, file_path, func.line_start, 
                        func.parameters, func.metadata
                    )
                    
                    # Create CONTAINS relationship
                    self.builder.create_contains_relationship(
                        file_path, func.name, "Function"
                    )
                
                # Create class nodes and relationships
                for cls in parsed.classes:
                    class_id = self.builder.create_class_node(
                        cls.name, file_path, cls.line_start, cls.metadata
                    )
                    
                    # Create CONTAINS relationship
                    self.builder.create_contains_relationship(
                        file_path, cls.name, "Class"
                    )
                    
                    # Create inheritance relationships
                    if hasattr(cls.metadata, 'bases'):
                        for base in cls.metadata.get('bases', []):
                            # This is simplified - in reality you'd need to resolve the base class
                            try:
                                self.builder.create_inheritance_relationship(
                                    cls.name, base, file_path, file_path  # Simplified
                                )
                            except Exception as e:
                                logger.debug(f"Could not create inheritance relationship: {e}")
            
            # 3. Create import relationships
            self._create_import_relationships_from_files(source_files)
            
            logger.info("Repository graph built successfully")
            
        except Exception as e:
            logger.error(f"Failed to build repository graph: {e}")
            raise

    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the graph database.
        
        Returns:
            Dictionary containing node counts, relationship counts, and detailed breakdowns
        """
        try:
            stats = {}
            
            # 1. Total node count
            node_count_query = "MATCH (n) RETURN count(n) as total_nodes"
            result = self.connection.execute_query(node_count_query)
            stats['total_nodes'] = result[0]['total_nodes'] if result else 0
            
            # 2. Total relationship count
            rel_count_query = "MATCH ()-[r]->() RETURN count(r) as total_relationships"
            result = self.connection.execute_query(rel_count_query)
            stats['total_relationships'] = result[0]['total_relationships'] if result else 0
            
            # 3. Node counts by label
            node_labels_query = """
            CALL db.labels() YIELD label
            CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {}) 
            YIELD value
            RETURN label, value.count as count
            """
            
            # Fallback query if APOC is not available
            simple_labels_query = """
            MATCH (n)
            RETURN labels(n) as node_labels, count(n) as count
            """
            
            try:
                # Try APOC version first
                result = self.connection.execute_query(node_labels_query)
                stats['nodes_by_label'] = {record['label']: record['count'] for record in result}
            except:
                # Fallback to manual counting
                result = self.connection.execute_query(simple_labels_query)
                label_counts = {}
                for record in result:
                    labels = record['node_labels']
                    count = record['count']
                    # Handle nodes with multiple labels
                    for label in labels:
                        label_counts[label] = label_counts.get(label, 0) + count
                stats['nodes_by_label'] = label_counts
            
            # 4. Relationship counts by type
            rel_types_query = """
            MATCH ()-[r]->()
            RETURN type(r) as relationship_type, count(r) as count
            ORDER BY count DESC
            """
            result = self.connection.execute_query(rel_types_query)
            stats['relationships_by_type'] = {record['relationship_type']: record['count'] for record in result}
            
            # 5. Additional detailed statistics
            
            # Files by language
            files_by_lang_query = """
            MATCH (f:File)
            RETURN f.language as language, count(f) as count
            ORDER BY count DESC
            """
            result = self.connection.execute_query(files_by_lang_query)
            stats['files_by_language'] = {record['language']: record['count'] for record in result if record['language']}
            
            # Functions per file statistics
            func_stats_query = """
            MATCH (f:File)
            OPTIONAL MATCH (f)-[:CONTAINS]->(func:Function)
            WITH f, count(func) as func_count
            RETURN 
                min(func_count) as min_functions_per_file,
                max(func_count) as max_functions_per_file,
                avg(func_count) as avg_functions_per_file,
                count(f) as total_files
            """
            result = self.connection.execute_query(func_stats_query)
            if result:
                stats['function_statistics'] = {
                    'min_functions_per_file': result[0]['min_functions_per_file'],
                    'max_functions_per_file': result[0]['max_functions_per_file'],
                    'avg_functions_per_file': round(result[0]['avg_functions_per_file'], 2) if result[0]['avg_functions_per_file'] else 0,
                    'total_files': result[0]['total_files']
                }
            
            # Classes with inheritance
            inheritance_query = """
            MATCH (child:Class)-[:INHERITS_FROM]->(parent:Class)
            RETURN count(child) as classes_with_inheritance,
                count(DISTINCT parent) as base_classes
            """
            result = self.connection.execute_query(inheritance_query)
            if result and result[0]['classes_with_inheritance']:
                stats['inheritance_statistics'] = {
                    'classes_with_inheritance': result[0]['classes_with_inheritance'],
                    'base_classes': result[0]['base_classes']
                }
            
            # Import relationships statistics
            import_stats_query = """
            MATCH (f1:File)-[i:IMPORTS]->(f2:File)
            WITH f1, count(i) as import_count
            RETURN 
                min(import_count) as min_imports_per_file,
                max(import_count) as max_imports_per_file,
                avg(import_count) as avg_imports_per_file,
                count(f1) as files_with_imports
            """
            result = self.connection.execute_query(import_stats_query)
            if result and result[0]['files_with_imports']:
                stats['import_statistics'] = {
                    'min_imports_per_file': result[0]['min_imports_per_file'],
                    'max_imports_per_file': result[0]['max_imports_per_file'],
                    'avg_imports_per_file': round(result[0]['avg_imports_per_file'], 2),
                    'files_with_imports': result[0]['files_with_imports']
                }
            
            logger.info(f"Retrieved graph statistics: {stats['total_nodes']} nodes, {stats['total_relationships']} relationships")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get graph statistics: {e}")
            return {
                'total_nodes': 0,
                'total_relationships': 0,
                'error': str(e)
            }

    def print_graph_statistics(self):
        """
        Print a formatted summary of graph statistics.
        """
        stats = self.get_graph_statistics()
        
        if 'error' in stats:
            print(f"Error retrieving statistics: {stats['error']}")
            return
        
        print("=" * 50)
        print("GRAPH DATABASE STATISTICS")
        print("=" * 50)
        
        print(f"Total Nodes: {stats['total_nodes']}")
        print(f"Total Relationships: {stats['total_relationships']}")
        print()
        
        if 'nodes_by_label' in stats:
            print("Nodes by Label:")
            for label, count in sorted(stats['nodes_by_label'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {label}: {count}")
            print()
        
        if 'relationships_by_type' in stats:
            print("Relationships by Type:")
            for rel_type, count in stats['relationships_by_type'].items():
                print(f"  {rel_type}: {count}")
            print()
        
        if 'files_by_language' in stats:
            print("Files by Language:")
            for lang, count in stats['files_by_language'].items():
                print(f"  {lang}: {count}")
            print()
        
        if 'function_statistics' in stats:
            func_stats = stats['function_statistics']
            print("Function Statistics:")
            print(f"  Total Files: {func_stats['total_files']}")
            print(f"  Functions per File - Min: {func_stats['min_functions_per_file']}, Max: {func_stats['max_functions_per_file']}, Avg: {func_stats['avg_functions_per_file']}")
            print()
        
        if 'inheritance_statistics' in stats:
            inh_stats = stats['inheritance_statistics']
            print("Inheritance Statistics:")
            print(f"  Classes with Inheritance: {inh_stats['classes_with_inheritance']}")
            print(f"  Base Classes: {inh_stats['base_classes']}")
            print()
        
        if 'import_statistics' in stats:
            imp_stats = stats['import_statistics']
            print("Import Statistics:")
            print(f"  Files with Imports: {imp_stats['files_with_imports']}")
            print(f"  Imports per File - Min: {imp_stats['min_imports_per_file']}, Max: {imp_stats['max_imports_per_file']}, Avg: {imp_stats['avg_imports_per_file']}")
        
        print("=" * 50)

    def _clear_repository_graph(self):
        """Clear existing graph data"""
        query = "MATCH (n) DETACH DELETE n"
        self.connection.execute_write(query)
        logger.info("Cleared existing graph data")

    def _create_import_relationships_from_files(self, source_files: List[str]):
        """Create import relationships by analyzing import statements"""
        for file_path in source_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple import detection for Python files
                if file_path.endswith('.py'):
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('import ') or line.startswith('from '):
                            imported_module = self._extract_import_module(line)
                            if imported_module:
                                # Try to find the corresponding file
                                imported_file = self._resolve_import_to_file(imported_module, file_path)
                                if imported_file:
                                    try:
                                        self.builder.create_import_relationship(
                                            file_path, imported_file, "module"
                                        )
                                    except Exception as e:
                                        logger.debug(f"Could not create import relationship: {e}")
                        
            except Exception as e:
                logger.warning(f"Failed to analyze imports in {file_path}: {e}")

    def _extract_import_module(self, import_line: str) -> Optional[str]:
        """
        Extract the module name from an import statement.
        
        Args:
            import_line: A line containing an import statement
            
        Returns:
            The module name or None if not found
            
        Examples:
            "import os" -> "os"
            "from pathlib import Path" -> "pathlib"
            "from .utils import scan_repository" -> "utils"
            "import package.submodule" -> "package.submodule"
        """
        import_line = import_line.strip()
        
        # Handle "import module" or "import package.submodule"
        if import_line.startswith('import '):
            # Remove 'import ' and get the first module (before any comma or 'as')
            module_part = import_line[7:].strip()
            # Split by comma and take first, then split by 'as' and take first
            module = module_part.split(',')[0].split(' as ')[0].strip()
            return module
        
        # Handle "from module import something"
        elif import_line.startswith('from '):
            # Extract text between 'from ' and ' import'
            match = re.match(r'from\s+([^\s]+)\s+import', import_line)
            if match:
                module = match.group(1)
                # Handle relative imports by removing leading dots
                if module.startswith('.'):
                    # Remove leading dots for relative imports
                    module = module.lstrip('.')
                    return module if module else None
                return module
        
        return None
    
    def _resolve_import_to_file(self, module_name: str, current_file_path: str) -> Optional[str]:
        """
        Resolve an import module name to an actual file path within the repository.
        
        Args:
            module_name: The module name extracted from import statement
            current_file_path: Path of the file containing the import
            
        Returns:
            Absolute path to the imported file, or None if not found
        """
        if not module_name:
            return None
        
        # Skip standard library and common third-party modules
        stdlib_modules = {
            'os', 'sys', 'json', 'logging', 'pathlib', 'typing', 're', 'collections',
            'itertools', 'functools', 'datetime', 'math', 'random', 'urllib', 'http',
            'sqlite3', 'csv', 'xml', 'html', 'email', 'hashlib', 'base64', 'pickle',
            'threading', 'multiprocessing', 'subprocess', 'shutil', 'tempfile', 'glob',
            'argparse', 'configparser', 'unittest', 'pytest', 'numpy', 'pandas',
            'requests', 'flask', 'django', 'sqlalchemy', 'boto3', 'redis'
        }
        
        # Check if it's likely a standard library or third-party module
        root_module = module_name.split('.')[0]
        if root_module in stdlib_modules:
            return None
        
        current_dir = Path(current_file_path).parent
        
        # Try different resolution strategies
        possible_paths = []
        
        # 1. Direct file in same directory
        if '.' not in module_name:
            possible_paths.extend([
                current_dir / f"{module_name}.py",
                current_dir / module_name / "__init__.py"
            ])
        
        # 2. Package.submodule format
        else:
            parts = module_name.split('.')
            # Try as package/submodule.py
            possible_paths.append(current_dir / '/'.join(parts[:-1]) / f"{parts[-1]}.py")
            # Try as package/submodule/__init__.py
            possible_paths.append(current_dir / '/'.join(parts) / "__init__.py")
        
        # 3. Look in parent directories (common project structure)
        parent_dir = current_dir.parent
        if '.' not in module_name:
            possible_paths.extend([
                parent_dir / f"{module_name}.py",
                parent_dir / module_name / "__init__.py"
            ])
        else:
            parts = module_name.split('.')
            possible_paths.extend([
                parent_dir / '/'.join(parts[:-1]) / f"{parts[-1]}.py",
                parent_dir / '/'.join(parts) / "__init__.py"
            ])
        
        # 4. Look in project root (go up until we find setup.py, pyproject.toml, or .git)
        project_root = self._find_project_root(current_file_path)
        if project_root:
            if '.' not in module_name:
                possible_paths.extend([
                    project_root / f"{module_name}.py",
                    project_root / module_name / "__init__.py"
                ])
            else:
                parts = module_name.split('.')
                possible_paths.extend([
                    project_root / '/'.join(parts[:-1]) / f"{parts[-1]}.py",
                    project_root / '/'.join(parts) / "__init__.py"
                ])
        
        # Check which file actually exists
        for path in possible_paths:
            if path.exists() and path.is_file():
                return str(path.resolve())
        
        return None
    
    def _find_project_root(self, file_path: str) -> Optional[Path]:
        """
        Find the project root by looking for common project markers.
        
        Args:
            file_path: Path to start searching from
            
        Returns:
            Path to project root or None if not found
        """
        current = Path(file_path).parent
        root_markers = {
            'setup.py', 'pyproject.toml', 'requirements.txt', 
            '.git', '.gitignore', 'Pipfile', 'poetry.lock',
            'manage.py'  # Django projects
        }
        
        # Limit search depth to avoid going too high
        max_depth = 10
        depth = 0
        
        while depth < max_depth and current != current.parent:
            # Check if any root marker exists in current directory
            if any((current / marker).exists() for marker in root_markers):
                return current
            current = current.parent
            depth += 1
        
        return None

    def close(self):
        """Close the Neo4j connection"""
        if hasattr(self, 'connection'):
            self.connection.close()

if __name__ == "__main__":
    graph_memory = Neo4jGraphMemory()

    repo_path = "/home/sujalnath/dev/projects/OrgGPT"

    graph_memory.build_repository_graph(repo_path)

    graph_memory.print_graph_statistics()