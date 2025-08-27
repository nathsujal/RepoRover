from typing import List, Dict, Any
from .db import get_db_session, Interaction

import logging
logger = logging.getLogger(__name__)

class EpisodicMemoryManager:
    def __init__(self):
        logger.info("Initializing Episodic Memory Manager...")
        self.session = get_db_session()

    def add_interaction(
        self,
        agent_name: str,
        interaction_type: str,
        content: str,
        interaction_metadata: Dict[str, Any] = None
    ):
        """Adds a new interaction to the episodic memory."""
        logger.info(f"Adding interaction: {interaction_type} - {content}")
        interaction = Interaction(
            agent_name=agent_name,
            interaction_type=interaction_type,
            content=content,
            interaction_metadata=interaction_metadata or {}
        )
        self.session.add(interaction)
        self.session.commit()

    def get_recent_interactions(self, limit: int = 10) -> List[Interaction]:
        """Retrieves the most recent interactions."""
        return self.session.query(Interaction).order_by(Interaction.timestamp.desc()).limit(limit).all()

    def get_interactions_by_agent(self, agent_name: str, limit: int = 10) -> List[Interaction]:
        """Retrieves the most recent interactions for a specific agent."""
        return self.session.query(Interaction)\
            .filter_by(agent_name=agent_name)\
            .order_by(Interaction.timestamp.desc())\
            .limit(limit)\
            .all()
