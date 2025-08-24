# src/memory/semantic_memory/graph_db/networkX_graph.py
from typing import Dict, List, Optional
import networkx as nx
from .base import GraphDatabase, Node, Relationship
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)

class NetworkXGraphDatabase(GraphDatabase):
    def __init__(self):
        self.graph = nx.DiGraph()
        logger.info("NetworkX Graph Initialized")
    
    def create_node(self, node: Node) -> None:
        # Prevent TypeError if 'type' is already in properties
        node_properties = node.properties.copy()
        self.graph.add_node(node.id, **node_properties)

    def get_node(self, node_id: str) -> Optional[Node]:
        node_data = self.graph.nodes.get(node_id)
        if not node_data:
            return None
        
        # Safely get type and remove it from properties dict for pydantic model
        node_type = node_data.pop('type', 'unknown') # Default to 'unknown' if type is missing
        return Node(id=node_id, type=node_type, properties=node_data)

    def create_relationship(self, rel: Relationship) -> None:
        self.graph.add_edge(rel.source_id, rel.target_id, type=rel.type, **rel.properties)

    def clear(self) -> None:
        """Clears all nodes and edges from the graph."""
        self.graph.clear()
        logger.info("NetworkX graph has been cleared.")
        
    def find_nodes(self, labels: List[str] = None, properties: Dict = None) -> List[Node]:
        matching_node_ids = [
            node_id for node_id, data in self.graph.nodes(data=True)
            if (not labels or data.get('type') in labels) and \
               (not properties or all(data.get(key) == value for key, value in properties.items()))
        ]
        # Get the full Node object for each matching ID
        return [self.get_node(node_id) for node_id in matching_node_ids if self.get_node(node_id)]

    def find_callers(self, node_id: str) -> List[str]:
        """Finds all nodes that have an edge pointing to the given node."""
        if node_id not in self.graph:
            return []
        return list(self.graph.predecessors(node_id))

    def find_callees(self, node_id: str) -> List[str]:
        """Finds all nodes that the given node has an edge pointing to."""
        if node_id not in self.graph:
            return []
        return list(self.graph.successors(node_id))

    def display(self) -> None:
        # Drawing a large graph can be slow and unreadable. Consider adding a check.
        if len(self.graph) < 100:
            nx.draw(self.graph, with_labels=True, node_color="lightblue", node_size=500)
            plt.show()
        else:
            logger.warning("Graph has too many nodes to display.")