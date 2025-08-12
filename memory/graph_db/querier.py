class RepoGraphQuerier:
    def __init__(self, neo4j_connection):
        self.neo4j = neo4j_connection
        
    def find_function_dependencies(self, function_name: str, max_depth: int = 3):
        """Find all functions that a given function depends on"""
        query = """
        MATCH (func:Function {name: $name})-[:CALLS*1..$max_depth]->(dependency:Function)
        RETURN DISTINCT dependency.name as dep_name, 
               dependency.file_path as dep_file,
               length(shortestPath((func)-[:CALLS*]->(dependency))) as depth
        ORDER BY depth, dep_name
        """
        
        return self.neo4j.execute_query(query, {
            "name": function_name, 
            "max_depth": max_depth
        })
    
    def find_circular_dependencies(self):
        """Find circular import dependencies"""
        query = """
        MATCH (f1:File)-[:IMPORTS*2..10]->(f1)
        WITH f1, length(shortestPath((f1)-[:IMPORTS*]->(f1))) as cycle_length
        RETURN f1.path as file_path, cycle_length
        ORDER BY cycle_length
        """
        
        return self.neo4j.execute_query(query)
    
    def find_most_important_functions(self, limit: int = 10):
        """Find functions that are called most frequently"""
        query = """
        MATCH (f:Function)<-[r:CALLS]-(caller)
        WITH f, sum(r.frequency) as total_calls, count(caller) as caller_count
        RETURN f.name as function_name,
               f.file_path as file_path,
               total_calls,
               caller_count,
               (total_calls * caller_count) as importance_score
        ORDER BY importance_score DESC
        LIMIT $limit
        """
        
        return self.neo4j.execute_query(query, {"limit": limit})
    
    def find_orphaned_functions(self):
        """Find functions that are never called"""
        query = """
        MATCH (f:Function)
        WHERE NOT (f)<-[:CALLS]-()
        AND f.name <> "main"
        AND NOT f.name STARTS WITH "__"
        RETURN f.name as function_name, f.file_path as file_path
        ORDER BY f.file_path, f.name
        """
        
        return self.neo4j.execute_query(query)
    
    def get_file_impact_analysis(self, file_path: str, max_depth: int = 5):
        """Find all files that would be affected if this file changes"""
        query = """
        MATCH (target:File {path: $file_path})<-[:IMPORTS*1..$max_depth]-(dependent:File)
        RETURN DISTINCT dependent.path as affected_file,
               length(shortestPath((dependent)-[:IMPORTS*]->(target))) as dependency_depth
        ORDER BY dependency_depth, affected_file
        """
        
        return self.neo4j.execute_query(query, {
            "file_path": file_path,
            "max_depth": max_depth
        })
    
    def find_related_code(self, search_term: str, limit: int = 20):
        """Find all code elements related to a search term"""
        query = """
        MATCH (n)
        WHERE toLower(n.name) CONTAINS toLower($term) 
           OR toLower(n.path) CONTAINS toLower($term)
           OR toLower(n.docstring) CONTAINS toLower($term)
        OPTIONAL MATCH (n)-[r]-(related)
        RETURN labels(n) as node_type,
               n.name as name,
               n.path as path,
               n.docstring as docstring,
               collect(DISTINCT {
                   type: type(r),
                   related_name: related.name,
                   related_type: labels(related)[0]
               }) as relationships
        LIMIT $limit
        """
        
        return self.neo4j.execute_query(query, {
            "term": search_term,
            "limit": limit
        })

    def find_code_relationships(self, query_type: str, entity_name: str):
        """Find relationships for a specific code entity"""
        if query_type == "function_callers":
            return self.find_function_callers(entity_name)
        elif query_type == "function_callees":
            return self.find_function_callees(entity_name)
        elif query_type == "class_hierarchy":
            return self.find_class_hierarchy(entity_name)
        elif query_type == "file_dependencies":
            return self.find_file_dependencies(entity_name)
        else:
            return self.find_related_code(entity_name)

    def find_function_callers(self, function_name: str):
        """Find all functions that call a specific function"""
        query = """
        MATCH (caller:Function)-[r:CALLS]->(func:Function {name: $name})
        RETURN caller.name as caller_name,
               caller.file_path as caller_file,
               r.frequency as call_frequency,
               r.last_seen as last_called
        ORDER BY r.frequency DESC
        """
        
        return self.neo4j.execute_query(query, {"name": function_name})

    def find_function_callees(self, function_name: str):
        """Find all functions called by a specific function"""
        query = """
        MATCH (func:Function {name: $name})-[r:CALLS]->(called:Function)
        RETURN called.name as called_name,
               called.file_path as called_file,
               r.frequency as call_frequency,
               r.last_seen as last_called
        ORDER BY r.frequency DESC
        """
        
        return self.neo4j.execute_query(query, {"name": function_name})

    def find_class_hierarchy(self, class_name: str):
        """Find the complete inheritance hierarchy for a class"""
        query = """
        MATCH (cls:Class {name: $name})
        OPTIONAL MATCH (cls)-[:INHERITS_FROM*]->(ancestor:Class)
        OPTIONAL MATCH (descendant:Class)-[:INHERITS_FROM*]->(cls)
        RETURN cls.name as class_name,
               cls.file_path as file_path,
               collect(DISTINCT ancestor.name) as ancestors,
               collect(DISTINCT descendant.name) as descendants
        """
        
        return self.neo4j.execute_query(query, {"name": class_name})

    def find_file_dependencies(self, file_path: str):
        """Find what a file imports and what imports it"""
        query = """
        MATCH (file:File {path: $path})
        OPTIONAL MATCH (file)-[r1:IMPORTS]->(imported:File)
        OPTIONAL MATCH (importer:File)-[r2:IMPORTS]->(file)
        RETURN file.path as file_path,
               collect(DISTINCT {
                   file: imported.path,
                   type: r1.import_type,
                   alias: r1.alias
               }) as imports,
               collect(DISTINCT importer.path) as imported_by
        """
        
        return self.neo4j.execute_query(query, {"path": file_path})

    def general_search(self, search_term: str):
        """General search across all entities"""
        return self.find_related_code(search_term)

    def get_repository_statistics(self):
        """Get overall repository statistics"""
        query = """
        MATCH (f:File) WITH count(f) as file_count
        MATCH (func:Function) WITH file_count, count(func) as function_count
        MATCH (cls:Class) WITH file_count, function_count, count(cls) as class_count
        MATCH ()-[r:CALLS]->() WITH file_count, function_count, class_count, count(r) as call_count
        MATCH ()-[r2:IMPORTS]->() WITH file_count, function_count, class_count, call_count, count(r2) as import_count
        RETURN file_count, function_count, class_count, call_count, import_count
        """
        
        return self.neo4j.execute_query(query)