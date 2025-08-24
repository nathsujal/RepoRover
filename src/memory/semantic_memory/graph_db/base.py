# src/memory/semantic_memory/graph_db/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class Node(BaseModel):
    id: str
    type: str
    properties: Dict[str, Any]

class Relationship(BaseModel):
    source_id: str
    target_id: str
    type: str
    properties: Dict[str, Any] = {}

class GraphDatabase(ABC):
    @abstractmethod
    def create_node(self, node: Node) -> None:
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[Node]:
        pass
    
    @abstractmethod
    def create_relationship(self, rel: Relationship) -> None:
        pass
    
    @abstractmethod
    def find_nodes(self, labels: List[str] = None, properties: Dict = None) -> List[Node]:
        pass