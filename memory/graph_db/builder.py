from pathlib import Path
from datetime import datetime
from typing import Dict, List

class RepoGraphBuilder:
    def __init__(self, neo4j_connection):
        self.neo4j = neo4j_connection
        
    def create_file_node(self, file_path: str, language: str, metadata: Dict) -> int:
        """Create a file node"""
        query = """
        MERGE (f:File {path: $path})
        SET f.name = $name,
            f.language = $language,
            f.size = $size,
            f.last_modified = datetime($last_modified),
            f.lines_of_code = $lines_of_code,
            f.created = CASE WHEN f.created IS NULL THEN datetime() ELSE f.created END,
            f.updated = datetime()
        RETURN elementId(f) as node_id
        """
        
        parameters = {
            "path": file_path,
            "name": Path(file_path).name,
            "language": language,
            "size": metadata.get("size", 0),
            "last_modified": metadata.get("last_modified", datetime.now().isoformat()),
            "lines_of_code": metadata.get("lines_of_code", 0)
        }
        
        result = self.neo4j.execute_write(query, parameters)
        return result[0]["node_id"] if result else None
    
    def create_function_node(self, name: str, file_path: str, line_start: int, 
                           parameters: List[str], metadata: Dict) -> int:
        """Create a function node"""
        query = """
        MERGE (func:Function {name: $name, file_path: $file_path})
        SET func.line_start = $line_start,
            func.line_end = $line_end,
            func.parameters = $parameters,
            func.return_type = $return_type,
            func.complexity = $complexity,
            func.is_async = $is_async,
            func.is_private = $is_private,
            func.docstring = $docstring,
            func.created = CASE WHEN func.created IS NULL THEN datetime() ELSE func.created END,
            func.updated = datetime()
        RETURN elementId(func) as node_id
        """
        
        params = {
            "name": name,
            "file_path": file_path,
            "line_start": line_start,
            "line_end": metadata.get("line_end"),
            "parameters": parameters,
            "return_type": metadata.get("return_type", "unknown"),
            "complexity": metadata.get("complexity", 1),
            "is_async": metadata.get("is_async", False),
            "is_private": name.startswith("_"),
            "docstring": metadata.get("docstring", "")
        }
        
        result = self.neo4j.execute_write(query, params)
        return result[0]["node_id"] if result else None

    def create_class_node(self, name: str, file_path: str, line_start: int, metadata: Dict) -> int:
        """Create a class node"""
        query = """
        MERGE (cls:Class {name: $name, file_path: $file_path})
        SET cls.line_start = $line_start,
            cls.line_end = $line_end,
            cls.is_abstract = $is_abstract,
            cls.access_modifier = $access_modifier,
            cls.docstring = $docstring,
            cls.created = CASE WHEN cls.created IS NULL THEN datetime() ELSE cls.created END,
            cls.updated = datetime()
        RETURN elementId(cls) as node_id
        """
        
        params = {
            "name": name,
            "file_path": file_path,
            "line_start": line_start,
            "line_end": metadata.get("line_end"),
            "is_abstract": metadata.get("is_abstract", False),
            "access_modifier": metadata.get("access_modifier", "public"),
            "docstring": metadata.get("docstring", "")
        }
        
        result = self.neo4j.execute_write(query, params)
        return result[0]["node_id"] if result else None

    def create_module_node(self, name: str, package: str, path: str, module_type: str = "library") -> int:
        """Create a module node"""
        query = """
        MERGE (mod:Module {name: $name, package: $package})
        SET mod.path = $path,
            mod.type = $type,
            mod.created = CASE WHEN mod.created IS NULL THEN datetime() ELSE mod.created END,
            mod.updated = datetime()
        RETURN elementId(mod) as node_id
        """
        
        params = {
            "name": name,
            "package": package,
            "path": path,
            "type": module_type
        }
        
        result = self.neo4j.execute_write(query, params)
        return result[0]["node_id"] if result else None
        
    def create_import_relationship(self, from_file_path: str, to_file_path: str, 
                                 import_type: str = "module", alias: str = None):
        """Create an IMPORTS relationship between files"""
        query = """
        MATCH (from:File {path: $from_path})
        MATCH (to:File {path: $to_path})
        MERGE (from)-[r:IMPORTS]->(to)
        SET r.import_type = $import_type,
            r.alias = $alias,
            r.last_seen = datetime(),
            r.frequency = COALESCE(r.frequency, 0) + 1
        """
        
        self.neo4j.execute_write(query, {
            "from_path": from_file_path,
            "to_path": to_file_path,
            "import_type": import_type,
            "alias": alias
        })
    
    def create_function_call_relationship(self, caller_func: Dict, called_func: Dict, frequency: int = 1):
        """Create a CALLS relationship between functions"""
        query = """
        MATCH (caller:Function {name: $caller_name, file_path: $caller_file})
        MATCH (called:Function {name: $called_name, file_path: $called_file})
        MERGE (caller)-[r:CALLS]->(called)
        SET r.frequency = COALESCE(r.frequency, 0) + $frequency,
            r.last_seen = datetime()
        """
        
        self.neo4j.execute_write(query, {
            "caller_name": caller_func["name"],
            "caller_file": caller_func["file_path"],
            "called_name": called_func["name"], 
            "called_file": called_func["file_path"],
            "frequency": frequency
        })

    def create_inheritance_relationship(self, child_class: str, parent_class: str, 
                                      child_file: str, parent_file: str):
        """Create an INHERITS_FROM relationship between classes"""
        query = """
        MATCH (child:Class {name: $child_name, file_path: $child_file})
        MATCH (parent:Class {name: $parent_name, file_path: $parent_file})
        MERGE (child)-[:INHERITS_FROM]->(parent)
        """
        
        self.neo4j.execute_write(query, {
            "child_name": child_class,
            "child_file": child_file,
            "parent_name": parent_class,
            "parent_file": parent_file
        })

    def create_contains_relationship(self, file_path: str, entity_name: str, entity_type: str):
        """Create a CONTAINS relationship between file and code entity"""
        query = f"""
        MATCH (file:File {{path: $file_path}})
        MATCH (entity:{entity_type} {{name: $entity_name, file_path: $file_path}})
        MERGE (file)-[:CONTAINS]->(entity)
        """
        
        self.neo4j.execute_write(query, {
            "file_path": file_path,
            "entity_name": entity_name
        })

    def create_method_relationship(self, class_name: str, method_name: str, file_path: str):
        """Create a HAS_METHOD relationship between class and method"""
        query = """
        MATCH (cls:Class {name: $class_name, file_path: $file_path})
        MATCH (method:Function {name: $method_name, file_path: $file_path})
        MERGE (cls)-[:HAS_METHOD]->(method)
        """
        
        self.neo4j.execute_write(query, {
            "class_name": class_name,
            "method_name": method_name,
            "file_path": file_path
        })