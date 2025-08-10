import sqlite3
import json
import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import uuid

@dataclass
class MemoryEntry:
    """Represents a single memory entry."""
    id: str
    timestamp: datetime.datetime
    agent_name: str
    event_type: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    importance: float = 1.0

class EpisodicMemory:
    """
    Manages episodic memory - storing conversation history, experiences,
    and temporal information about agent interactions.
    """
    
    def __init__(self, db_path: str = "data/episodic_memory.db"):
        """
        Initialize the episodic memory system.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    importance REAL DEFAULT 1.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_name ON memories(agent_name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_type ON memories(event_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)
            """)
    
    def store_memory(self, agent_name: str, event_type: str, content: Dict[str, Any], 
                    metadata: Optional[Dict[str, Any]] = None, importance: float = 1.0) -> str:
        """
        Store a new memory entry.
        
        Args:
            agent_name (str): Name of the agent that generated this memory
            event_type (str): Type of event (e.g., 'conversation', 'task_completion', 'error')
            content (Dict[str, Any]): The main content of the memory
            metadata (Optional[Dict[str, Any]]): Additional metadata
            importance (float): Importance score (0.0 to 1.0)
            
        Returns:
            str: The ID of the stored memory
        """
        memory_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()
        
        memory_entry = MemoryEntry(
            id=memory_id,
            timestamp=datetime.datetime.now(),
            agent_name=agent_name,
            event_type=event_type,
            content=content,
            metadata=metadata or {},
            importance=importance
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO memories (id, timestamp, agent_name, event_type, content, metadata, importance)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                memory_entry.id,
                memory_entry.timestamp.isoformat(),
                memory_entry.agent_name,
                memory_entry.event_type,
                json.dumps(memory_entry.content),
                json.dumps(memory_entry.metadata),
                memory_entry.importance
            ))
        
        return memory_id
    
    def retrieve_memories(self, agent_name: Optional[str] = None, 
                         event_type: Optional[str] = None,
                         limit: int = 50,
                         min_importance: float = 0.0) -> List[MemoryEntry]:
        """
        Retrieve memories based on filters.
        
        Args:
            agent_name (Optional[str]): Filter by agent name
            event_type (Optional[str]): Filter by event type
            limit (int): Maximum number of memories to retrieve
            min_importance (float): Minimum importance threshold
            
        Returns:
            List[MemoryEntry]: List of memory entries
        """
        query = "SELECT * FROM memories WHERE importance >= ?"
        params = [min_importance]
        
        if agent_name:
            query += " AND agent_name = ?"
            params.append(agent_name)
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        memories = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            for row in cursor.fetchall():
                memory = MemoryEntry(
                    id=row[0],
                    timestamp=datetime.datetime.fromisoformat(row[1]),
                    agent_name=row[2],
                    event_type=row[3],
                    content=json.loads(row[4]),
                    metadata=json.loads(row[5]),
                    importance=row[6]
                )
                memories.append(memory)
        
        return memories
    
    def get_conversation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent conversation history.
        
        Args:
            limit (int): Maximum number of conversation entries to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of conversation entries
        """
        memories = self.retrieve_memories(event_type="conversation", limit=limit)
        return [asdict(memory) for memory in memories]
    
    def search_memories(self, query: str, limit: int = 20) -> List[MemoryEntry]:
        """
        Search memories by content (simple text search).
        
        Args:
            query (str): Search query
            limit (int): Maximum number of results
            
        Returns:
            List[MemoryEntry]: List of matching memory entries
        """
        query_lower = query.lower()
        all_memories = self.retrieve_memories(limit=1000)  # Get more for search
        
        matching_memories = []
        for memory in all_memories:
            # Search in content
            content_str = json.dumps(memory.content).lower()
            if query_lower in content_str:
                matching_memories.append(memory)
            
            # Search in metadata
            metadata_str = json.dumps(memory.metadata).lower()
            if query_lower in metadata_str:
                matching_memories.append(memory)
        
        # Sort by importance and recency
        matching_memories.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
        return matching_memories[:limit]
    
    def update_importance(self, memory_id: str, new_importance: float):
        """
        Update the importance score of a memory.
        
        Args:
            memory_id (str): ID of the memory to update
            new_importance (float): New importance score
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE memories SET importance = ? WHERE id = ?
            """, (new_importance, memory_id))
    
    def delete_memory(self, memory_id: str):
        """
        Delete a memory entry.
        
        Args:
            memory_id (str): ID of the memory to delete
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored memories.
        
        Returns:
            Dict[str, Any]: Memory statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            agents = conn.execute("SELECT DISTINCT agent_name FROM memories").fetchall()
            event_types = conn.execute("SELECT DISTINCT event_type FROM memories").fetchall()
            avg_importance = conn.execute("SELECT AVG(importance) FROM memories").fetchone()[0]
            
            return {
                "total_memories": total,
                "unique_agents": len(agents),
                "unique_event_types": len(event_types),
                "average_importance": avg_importance or 0.0,
                "agents": [agent[0] for agent in agents],
                "event_types": [event[0] for event in event_types]
            }

# Example usage
if __name__ == "__main__":
    episodic_memory = EpisodicMemory()
    
    # Store some example memories
    episodic_memory.store_memory(
        agent_name="Coordinator",
        event_type="conversation",
        content={"user_message": "Hello", "response": "Hi there!"},
        metadata={"session_id": "123"},
        importance=0.8
    )
    
    # Retrieve memories
    memories = episodic_memory.retrieve_memories(agent_name="Coordinator")
    print(f"Retrieved {len(memories)} memories")
    
    # Get stats
    stats = episodic_memory.get_memory_stats()
    print(f"Memory stats: {stats}")
