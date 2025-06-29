"""
Database configuration and session management for the User API.

This module handles SQLAlchemy database setup, session management,
and provides dependency injection for FastAPI.
"""
import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from models import Base

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/users.db")

# Create engine with appropriate settings
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true"
)

# Configure SQLite for better concurrency
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance and reliability"""
    if 'sqlite' in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        # Set WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        # Set reasonable timeout
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    try:
        # Ensure data directory exists
        db_dir = os.path.dirname(DATABASE_URL.replace("sqlite:///", ""))
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def get_db() -> Session:
    """
    Dependency function to get database session.
    
    This function is used as a dependency in FastAPI endpoints
    to provide database session with automatic cleanup.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize database with tables and any required seed data"""
    try:
        create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# Health check function
def check_db_health() -> bool:
    """
    Check if database is accessible and healthy.
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        db = SessionLocal()
        # Simple query to test connection
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
