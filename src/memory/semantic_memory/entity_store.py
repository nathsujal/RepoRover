import sqlite3
from typing import Optional, List
from pydantic import BaseModel

import logging
logger = logging.getLogger(__name__)

class Entity(BaseModel):
    unique_id: str
    type: str
    summary: str
    details: str
    code: str
    source: str

class SQLiteEntityStore:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                unique_id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                summary TEXT,
                details TEXT,
                code TEXT,
                source TEXT
            )
        """)
        self.conn.commit()

    def add_entity(self, entity: Entity):
        with self.conn:
            self.cursor.execute(
                "INSERT OR REPLACE INTO entities VALUES (?, ?, ?, ?, ?, ?)",
                (entity.unique_id, entity.type, entity.summary, entity.details, entity.code, entity.source)
            )

    def get_entity(self, unique_id: str) -> Optional[Entity]:
        self.cursor.execute("SELECT * FROM entities WHERE unique_id=?", (unique_id,))
        row = self.cursor.fetchone()
        if row:
            return Entity(unique_id=row[0], type=row[1], summary=row[2], details=row[3], code=row[4], source=row[5])
        return None

    def find_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Finds all entities in the database matching a specific type."""
        self.cursor.execute("SELECT * FROM entities WHERE type=?", (entity_type,))
        rows = self.cursor.fetchall()

        return [Entity(unique_id=r[0], type=r[1], summary=r[2], details=r[3], code=r[4], source=r[5]) for r in rows]

    def clear(self) -> None:
        """Deletes all records from the entities table."""
        with self.conn:
            self.cursor.execute("DELETE FROM entities")
        logger.info("SQLite entity store has been cleared.")