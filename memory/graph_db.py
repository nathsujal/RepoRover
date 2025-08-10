import os
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("Neo4j driver not available. Install with: pip install neo4j")

@dataclass
class Node:
    """Represents a node in the knowledge graph."""
    id: str
    labels: List[str]
    properties: Dict[str, Any]

@dataclass
class Relationship:
    """Represents a relationship in the knowledge graph."""
    start_node: str
    end_node: str
    type: str
    properties: Dict[str, Any]

class Neo4jGraphDatabase:
    """
    Manages a knowledge graph database for storing relationships and entities.
    Uses Neo4j for graph operations.
    """
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 username: str = "neo4j", 
                 password: str = "password",
                 database: str = "neo4j"):
        """
        Initialize the graph database connection.
        
        Args:
            uri (str): Neo4j connection URI
            username (str): Database username
            password (str): Database password
            database (str): Database name
        """
        if not NEO4J_AVAILABLE:
            raise ImportError("Neo4j driver not available. Install with: pip install neo4j")
        
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        
        # Test connection
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            self._test_connection()
        except Exception as e:
            logging.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def _test_connection(self):
        """Test the database connection."""
        with self.driver.session(database=self.database) as session:
            result = session.run("RETURN 1 as test")
            result.single()
    
    def create_node(self, labels: List[str], properties: Dict[str, Any], 
                   node_id: Optional[str] = None) -> str:
        """
        Create a new node in the graph.
        
        Args:
            labels (List[str]): Node labels
            properties (Dict[str, Any]): Node properties
            node_id (Optional[str]): Custom node ID
            
        Returns:
            str: The created node ID
        """
        # Always ensure we have an id property
        if not node_id:
            import hashlib
            content = str(properties) + str(labels)
            node_id = hashlib.md5(content.encode()).hexdigest()[:12]
        
        properties['id'] = node_id
        
        with self.driver.session(database=self.database) as session:
            # Create labels string
            labels_str = ':'.join(labels)
            
            # Create properties string
            props_str = ', '.join([f"{k}: ${k}" for k in properties.keys()])
            
            query = f"CREATE (n:{labels_str} {{{props_str}}}) RETURN n.id as id"
            result = session.run(query, **properties)
            
            record = result.single()
            if record and record['id']:
                return record['id']
            else:
                return node_id
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """
        Retrieve a node by ID.
        
        Args:
            node_id (str): Node ID to retrieve
            
        Returns:
            Optional[Node]: Node data or None if not found
        """
        with self.driver.session(database=self.database) as session:
            query = "MATCH (n) WHERE n.id = $node_id RETURN n"
            result = session.run(query, node_id=node_id)
            record = result.single()
            
            if record:
                node = record['n']
                return Node(
                    id=node.get('id'),
                    labels=list(node.labels),
                    properties=dict(node)
                )
        
        return None
    
    def update_node(self, node_id: str, properties: Dict[str, Any]):
        """
        Update node properties.
        
        Args:
            node_id (str): Node ID to update
            properties (Dict[str, Any]): New properties
        """
        with self.driver.session(database=self.database) as session:
            props_str = ', '.join([f"n.{k} = ${k}" for k in properties.keys()])
            query = f"MATCH (n) WHERE n.id = $node_id SET {props_str}"
            session.run(query, node_id=node_id, **properties)
    
    def delete_node(self, node_id: str):
        """
        Delete a node and its relationships.
        
        Args:
            node_id (str): Node ID to delete
        """
        with self.driver.session(database=self.database) as session:
            query = "MATCH (n) WHERE n.id = $node_id DETACH DELETE n"
            session.run(query, node_id=node_id)
    
    def create_relationship(self, start_node_id: str, end_node_id: str, 
                          relationship_type: str, properties: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a relationship between two nodes.
        
        Args:
            start_node_id (str): ID of the start node
            end_node_id (str): ID of the end node
            relationship_type (str): Type of relationship
            properties (Optional[Dict[str, Any]]): Relationship properties
            
        Returns:
            str: Relationship ID
        """
        properties = properties or {}
        
        with self.driver.session(database=self.database) as session:
            props_str = ', '.join([f"{k}: ${k}" for k in properties.keys()]) if properties else ""
            props_clause = f"{{{props_str}}}" if props_str else ""
            
            query = f"""
            MATCH (a), (b) 
            WHERE a.id = $start_id AND b.id = $end_id 
            CREATE (a)-[r:{relationship_type} {props_clause}]->(b) 
            RETURN elementId(r) as rel_id
            """
            
            result = session.run(query, start_id=start_node_id, end_id=end_node_id, **properties)
            record = result.single()
            if record and record['rel_id'] is not None:
                return str(record['rel_id'])
            else:
                # Fallback: generate relationship ID
                import hashlib
                content = f"{start_node_id}_{end_node_id}_{relationship_type}"
                return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def get_relationships(self, node_id: str, direction: str = "both") -> List[Relationship]:
        """
        Get relationships for a node.
        
        Args:
            node_id (str): Node ID
            direction (str): 'incoming', 'outgoing', or 'both'
            
        Returns:
            List[Relationship]: List of relationships
        """
        with self.driver.session(database=self.database) as session:
            if direction == "incoming":
                query = """
                MATCH (a)-[r]->(b) 
                WHERE b.id = $node_id 
                RETURN a.id as start, b.id as end, type(r) as type, r as props
                """
            elif direction == "outgoing":
                query = """
                MATCH (a)-[r]->(b) 
                WHERE a.id = $node_id 
                RETURN a.id as start, b.id as end, type(r) as type, r as props
                """
            else:  # both
                query = """
                MATCH (a)-[r]-(b) 
                WHERE a.id = $node_id OR b.id = $node_id 
                RETURN a.id as start, b.id as end, type(r) as type, r as props
                """
            
            result = session.run(query, node_id=node_id)
            relationships = []
            
            for record in result:
                rel = Relationship(
                    start_node=record['start'],
                    end_node=record['end'],
                    type=record['type'],
                    properties=dict(record['props'])
                )
                relationships.append(rel)
            
            return relationships
    
    def search_nodes(self, labels: Optional[List[str]] = None, 
                    properties: Optional[Dict[str, Any]] = None,
                    limit: int = 100) -> List[Node]:
        """
        Search for nodes by labels and properties.
        
        Args:
            labels (Optional[List[str]]): Node labels to filter by
            properties (Optional[Dict[str, Any]]): Properties to filter by
            limit (int): Maximum number of results
            
        Returns:
            List[Node]: List of matching nodes
        """
        with self.driver.session(database=self.database) as session:
            # Build query
            query_parts = ["MATCH (n)"]
            params = {}
            
            if labels:
                labels_str = ':'.join(labels)
                query_parts.append(f"WHERE n:{labels_str}")
            
            if properties:
                if labels:
                    query_parts.append("AND")
                else:
                    query_parts.append("WHERE")
                
                prop_conditions = []
                for key, value in properties.items():
                    param_name = f"prop_{key}"
                    prop_conditions.append(f"n.{key} = ${param_name}")
                    params[param_name] = value
                
                query_parts.append(" AND ".join(prop_conditions))
            
            query_parts.append("RETURN n LIMIT $limit")
            params['limit'] = limit
            
            query = " ".join(query_parts)
            result = session.run(query, **params)
            
            nodes = []
            for record in result:
                node = record['n']
                nodes.append(Node(
                    id=node.get('id'),
                    labels=list(node.labels),
                    properties=dict(node)
                ))
            
            return nodes
    
    def execute_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a custom Cypher query.
        
        Args:
            query (str): Cypher query to execute
            parameters (Optional[Dict[str, Any]]): Query parameters
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        parameters = parameters or {}
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, **parameters)
            return [dict(record) for record in result]
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the graph database.
        
        Returns:
            Dict[str, Any]: Graph statistics
        """
        with self.driver.session(database=self.database) as session:
            # Node count
            node_count = session.run("MATCH (n) RETURN count(n) as count").single()['count']
            
            # Relationship count
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
            
            # Node labels
            labels_result = session.run("CALL db.labels() YIELD label RETURN collect(label) as labels")
            labels = labels_result.single()['labels']
            
            # Relationship types
            rel_types_result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as types")
            rel_types = rel_types_result.single()['types']
            
            return {
                'node_count': node_count,
                'relationship_count': rel_count,
                'node_labels': labels,
                'relationship_types': rel_types,
                'database': self.database
            }
    
    def clear_database(self):
        """Clear all nodes and relationships from the database."""
        with self.driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
    
    def create_index(self, label: str, property_name: str):
        """
        Create an index on a node property.
        
        Args:
            label (str): Node label
            property_name (str): Property name to index
        """
        with self.driver.session(database=self.database) as session:
            query = f"CREATE INDEX FOR (n:{label}) ON (n.{property_name})"
            session.run(query)
    
    def close(self):
        """Close the database connection."""
        if hasattr(self, 'driver'):
            self.driver.close()

# Fallback implementation for when Neo4j is not available
class MockGraphDatabase:
    """Mock implementation when Neo4j is not available."""
    
    def __init__(self, *args, **kwargs):
        self.nodes = {}
        self.relationships = []
        logging.warning("Using mock graph database. Install Neo4j for full functionality.")
    
    def create_node(self, labels, properties, node_id=None):
        if not node_id:
            node_id = f"node_{len(self.nodes)}"
        self.nodes[node_id] = Node(id=node_id, labels=labels, properties=properties)
        return node_id
    
    def get_node(self, node_id):
        return self.nodes.get(node_id)
    
    def create_relationship(self, start_node_id, end_node_id, relationship_type, properties=None):
        rel_id = f"rel_{len(self.relationships)}"
        rel = Relationship(start_node_id, end_node_id, relationship_type, properties or {})
        self.relationships.append(rel)
        return rel_id
    
    def get_graph_stats(self):
        return {
            'node_count': len(self.nodes),
            'relationship_count': len(self.relationships),
            'node_labels': list(set(label for node in self.nodes.values() for label in node.labels)),
            'relationship_types': list(set(rel.type for rel in self.relationships)),
            'database': 'mock'
        }
    
    def close(self):
        pass

# Use mock implementation if Neo4j is not available
if not NEO4J_AVAILABLE:
    GraphDatabase = MockGraphDatabase

# Example usage
if __name__ == "__main__":
    try:
        graph_db = GraphDatabase()
        
        # Create some example nodes
        person_id = graph_db.create_node(
            labels=['Person'],
            properties={'name': 'Alice', 'age': 30}
        )
        
        project_id = graph_db.create_node(
            labels=['Project'],
            properties={'name': 'RepoRover', 'type': 'AI Agent'}
        )
        
        # Create relationship
        graph_db.create_relationship(
            start_node_id=person_id,
            end_node_id=project_id,
            relationship_type='WORKS_ON',
            properties={'role': 'developer', 'since': '2024'}
        )
        
        # Get stats
        stats = graph_db.get_graph_stats()
        print(f"Graph stats: {stats}")
        
        graph_db.close()
        
    except Exception as e:
        print(f"Error: {e}")
        print("Using mock implementation...")
        graph_db = MockGraphDatabase()
        
        # Create some example nodes
        person_id = graph_db.create_node(
            labels=['Person'],
            properties={'name': 'Alice', 'age': 30}
        )
        
        project_id = graph_db.create_node(
            labels=['Project'],
            properties={'name': 'RepoRover', 'type': 'AI Agent'}
        )
        
        # Create relationship
        graph_db.create_relationship(
            start_node_id=person_id,
            end_node_id=project_id,
            relationship_type='WORKS_ON',
            properties={'role': 'developer', 'since': '2024'}
        )
        
        # Get stats
        stats = graph_db.get_graph_stats()
        print(f"Mock graph stats: {stats}")
