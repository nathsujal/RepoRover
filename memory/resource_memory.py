import os
import json
import sqlite3
import hashlib
import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import mimetypes

@dataclass
class Resource:
    """Represents a resource (file, URL, etc.) in the system."""
    id: str
    path: str
    resource_type: str
    metadata: Dict[str, Any]
    last_accessed: datetime.datetime
    access_count: int
    size: Optional[int] = None
    checksum: Optional[str] = None

class ResourceMemory:
    """
    Manages resource memory - tracking files, URLs, and other resources
    with metadata and access patterns.
    """
    
    def __init__(self, db_path: str = "data/resource_memory.db"):
        """
        Initialize the resource memory system.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    id TEXT PRIMARY KEY,
                    path TEXT UNIQUE NOT NULL,
                    resource_type TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    size INTEGER,
                    checksum TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_path ON resources(path)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_resource_type ON resources(resource_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_accessed ON resources(last_accessed)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_access_count ON resources(access_count)
            """)
    
    def add_resource(self, path: str, resource_type: str, 
                    metadata: Optional[Dict[str, Any]] = None,
                    resource_id: Optional[str] = None) -> str:
        """
        Add a new resource to the memory.
        
        Args:
            path (str): Path or URL of the resource
            resource_type (str): Type of resource (file, url, api, etc.)
            metadata (Optional[Dict[str, Any]]): Additional metadata
            resource_id (Optional[str]): Custom resource ID
            
        Returns:
            str: The resource ID
        """
        if not resource_id:
            resource_id = self._generate_resource_id(path)
        
        metadata = metadata or {}
        now = datetime.datetime.now()
        
        # Get file size and checksum if it's a local file
        size = None
        checksum = None
        if resource_type == "file" and os.path.exists(path):
            try:
                size = os.path.getsize(path)
                checksum = self._calculate_checksum(path)
            except (OSError, IOError):
                pass
        
        # Add file type detection
        if resource_type == "file":
            file_type = mimetypes.guess_type(path)[0]
            if file_type:
                metadata['mime_type'] = file_type
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO resources 
                (id, path, resource_type, metadata, last_accessed, access_count, size, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                resource_id,
                path,
                resource_type,
                json.dumps(metadata),
                now.isoformat(),
                0,
                size,
                checksum
            ))
        
        return resource_id
    
    def get_resource(self, resource_id: str) -> Optional[Resource]:
        """
        Retrieve a resource by ID.
        
        Args:
            resource_id (str): Resource ID to retrieve
            
        Returns:
            Optional[Resource]: Resource data or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM resources WHERE id = ?
            """, (resource_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_resource(row)
        
        return None
    
    def get_resource_by_path(self, path: str) -> Optional[Resource]:
        """
        Retrieve a resource by path.
        
        Args:
            path (str): Resource path to retrieve
            
        Returns:
            Optional[Resource]: Resource data or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM resources WHERE path = ?
            """, (path,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_resource(row)
        
        return None
    
    def update_resource_metadata(self, resource_id: str, metadata: Dict[str, Any]):
        """
        Update resource metadata.
        
        Args:
            resource_id (str): Resource ID to update
            metadata (Dict[str, Any]): New metadata
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE resources SET metadata = ? WHERE id = ?
            """, (json.dumps(metadata), resource_id))
    
    def record_access(self, resource_id: str):
        """
        Record that a resource was accessed.
        
        Args:
            resource_id (str): Resource ID that was accessed
        """
        now = datetime.datetime.now()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE resources 
                SET last_accessed = ?, access_count = access_count + 1 
                WHERE id = ?
            """, (now.isoformat(), resource_id))
    
    def search_resources(self, query: str, resource_type: Optional[str] = None, 
                        limit: int = 50) -> List[Resource]:
        """
        Search for resources by path or metadata.
        
        Args:
            query (str): Search query
            resource_type (Optional[str]): Filter by resource type
            limit (int): Maximum number of results
            
        Returns:
            List[Resource]: List of matching resources
        """
        query_lower = query.lower()
        
        with sqlite3.connect(self.db_path) as conn:
            sql = "SELECT * FROM resources WHERE (path LIKE ? OR metadata LIKE ?)"
            params = [f"%{query}%", f"%{query}%"]
            
            if resource_type:
                sql += " AND resource_type = ?"
                params.append(resource_type)
            
            sql += " ORDER BY access_count DESC, last_accessed DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(sql, params)
            return [self._row_to_resource(row) for row in cursor.fetchall()]
    
    def get_recent_resources(self, limit: int = 20) -> List[Resource]:
        """
        Get recently accessed resources.
        
        Args:
            limit (int): Maximum number of resources to retrieve
            
        Returns:
            List[Resource]: List of recently accessed resources
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM resources 
                ORDER BY last_accessed DESC 
                LIMIT ?
            """, (limit,))
            
            return [self._row_to_resource(row) for row in cursor.fetchall()]
    
    def get_popular_resources(self, limit: int = 20) -> List[Resource]:
        """
        Get most frequently accessed resources.
        
        Args:
            limit (int): Maximum number of resources to retrieve
            
        Returns:
            List[Resource]: List of most popular resources
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM resources 
                ORDER BY access_count DESC 
                LIMIT ?
            """, (limit,))
            
            return [self._row_to_resource(row) for row in cursor.fetchall()]
    
    def get_resources_by_type(self, resource_type: str, limit: int = 100) -> List[Resource]:
        """
        Get resources of a specific type.
        
        Args:
            resource_type (str): Type of resources to retrieve
            limit (int): Maximum number of resources to retrieve
            
        Returns:
            List[Resource]: List of resources of the specified type
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM resources 
                WHERE resource_type = ? 
                ORDER BY last_accessed DESC 
                LIMIT ?
            """, (resource_type, limit))
            
            return [self._row_to_resource(row) for row in cursor.fetchall()]
    
    def delete_resource(self, resource_id: str):
        """
        Delete a resource from memory.
        
        Args:
            resource_id (str): Resource ID to delete
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM resources WHERE id = ?", (resource_id,))
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored resources.
        
        Returns:
            Dict[str, Any]: Resource statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
            types = conn.execute("SELECT DISTINCT resource_type FROM resources").fetchall()
            total_size = conn.execute("SELECT SUM(size) FROM resources WHERE size IS NOT NULL").fetchone()[0] or 0
            total_accesses = conn.execute("SELECT SUM(access_count) FROM resources").fetchone()[0] or 0
            
            type_counts = {}
            for resource_type in types:
                count = conn.execute("""
                    SELECT COUNT(*) FROM resources WHERE resource_type = ?
                """, (resource_type[0],)).fetchone()[0]
                type_counts[resource_type[0]] = count
            
            return {
                "total_resources": total,
                "resource_types": type_counts,
                "total_size_bytes": total_size,
                "total_accesses": total_accesses,
                "unique_types": len(types)
            }
    
    def get_related_resources(self, resource_id: str, limit: int = 10) -> List[Resource]:
        """
        Get resources that might be related based on path similarity or metadata.
        
        Args:
            resource_id (str): Resource ID to find related resources for
            limit (int): Maximum number of related resources to retrieve
            
        Returns:
            List[Resource]: List of potentially related resources
        """
        resource = self.get_resource(resource_id)
        if not resource:
            return []
        
        # Find resources with similar paths or metadata
        related = []
        
        # Search by path similarity
        path_parts = Path(resource.path).parts
        if len(path_parts) > 1:
            # Look for resources in the same directory
            parent_dir = str(Path(resource.path).parent)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM resources 
                    WHERE path LIKE ? AND id != ?
                    ORDER BY last_accessed DESC 
                    LIMIT ?
                """, (f"{parent_dir}%", resource_id, limit))
                
                related.extend([self._row_to_resource(row) for row in cursor.fetchall()])
        
        # Search by metadata similarity
        if resource.metadata:
            metadata_keys = list(resource.metadata.keys())
            if metadata_keys:
                with sqlite3.connect(self.db_path) as conn:
                    for key in metadata_keys[:3]:  # Check first 3 metadata keys
                        cursor = conn.execute("""
                            SELECT * FROM resources 
                            WHERE metadata LIKE ? AND id != ?
                            ORDER BY last_accessed DESC 
                            LIMIT ?
                        """, (f"%{key}%", resource_id, limit // 2))
                        
                        related.extend([self._row_to_resource(row) for row in cursor.fetchall()])
        
        # Remove duplicates and limit results
        seen_ids = set()
        unique_related = []
        for res in related:
            if res.id not in seen_ids and len(unique_related) < limit:
                seen_ids.add(res.id)
                unique_related.append(res)
        
        return unique_related
    
    def _row_to_resource(self, row) -> Resource:
        """Convert a database row to a Resource object."""
        return Resource(
            id=row[0],
            path=row[1],
            resource_type=row[2],
            metadata=json.loads(row[3]),
            last_accessed=datetime.datetime.fromisoformat(row[4]),
            access_count=row[5],
            size=row[6],
            checksum=row[7]
        )
    
    def _generate_resource_id(self, path: str) -> str:
        """Generate a unique resource ID based on path."""
        return hashlib.md5(path.encode()).hexdigest()[:12]
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of a file."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (OSError, IOError):
            return None
    
    def cleanup_invalid_resources(self) -> int:
        """
        Remove resources that no longer exist (for file resources).
        
        Returns:
            int: Number of resources removed
        """
        removed_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            # Get all file resources
            cursor = conn.execute("""
                SELECT id, path FROM resources WHERE resource_type = 'file'
            """)
            
            for row in cursor.fetchall():
                resource_id, path = row
                if not os.path.exists(path):
                    conn.execute("DELETE FROM resources WHERE id = ?", (resource_id,))
                    removed_count += 1
        
        return removed_count

# Example usage
if __name__ == "__main__":
    resource_memory = ResourceMemory()
    
    # Add some example resources
    resource_memory.add_resource(
        path="/path/to/example.py",
        resource_type="file",
        metadata={"language": "python", "purpose": "example"}
    )
    
    resource_memory.add_resource(
        path="https://api.example.com/data",
        resource_type="api",
        metadata={"method": "GET", "format": "json"}
    )
    
    # Record access
    resources = resource_memory.get_recent_resources()
    if resources:
        resource_memory.record_access(resources[0].id)
    
    # Get stats
    stats = resource_memory.get_resource_stats()
    print(f"Resource stats: {stats}")
    
    # Search resources
    results = resource_memory.search_resources("example")
    print(f"Found {len(results)} resources matching 'example'")
