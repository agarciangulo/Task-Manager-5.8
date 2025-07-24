"""
Centralized database connection management.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.config.settings import DATABASE_URL

# Create database engine
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    pool_pre_ping=True,
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    """
    Get a database session.
    
    Returns:
        Session: SQLAlchemy session instance
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 