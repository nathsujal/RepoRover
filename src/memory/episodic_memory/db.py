import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from src.core.config import settings

Base = declarative_base()

class Interaction(Base):
    __tablename__ = 'interactions'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    agent_name = Column(String, nullable=False)
    interaction_type = Column(String, nullable=False)  # e.g., 'user_request', 'agent_response', 'internal_thought'
    content = Column(String, nullable=False)
    interaction_metadata = Column(JSON, nullable=True)

def get_db_session():
    engine = create_engine(settings.EPISODIC_MEMORY_DB_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
