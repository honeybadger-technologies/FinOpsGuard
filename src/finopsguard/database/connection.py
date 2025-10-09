"""Database connection and session management."""

import os
import logging
from typing import Generator, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://finopsguard:finopsguard@localhost:5432/finopsguard'
)
DB_ENABLED = os.getenv('DB_ENABLED', 'false').lower() == 'true'
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '20'))
DB_POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))
DB_POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))

# Global engine and session factory
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def get_engine() -> Optional[Engine]:
    """
    Get database engine (singleton pattern).
    
    Returns:
        SQLAlchemy engine or None if database is disabled
    """
    global _engine
    
    if not DB_ENABLED:
        return None
    
    if _engine is None:
        try:
            _engine = create_engine(
                DATABASE_URL,
                poolclass=QueuePool,
                pool_size=DB_POOL_SIZE,
                max_overflow=DB_MAX_OVERFLOW,
                pool_timeout=DB_POOL_TIMEOUT,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=DB_POOL_RECYCLE,  # Recycle connections after 1 hour
                echo=os.getenv('DB_ECHO', 'false').lower() == 'true',
            )
            
            # Add event listener for connection
            @event.listens_for(_engine, "connect")
            def receive_connect(dbapi_conn, connection_record):
                logger.debug("Database connection established")
            
            logger.info(f"Database engine created: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
            
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            _engine = None
    
    return _engine


def get_session_factory() -> Optional[sessionmaker]:
    """
    Get session factory.
    
    Returns:
        SQLAlchemy sessionmaker or None if database is disabled
    """
    global _SessionLocal
    
    if not DB_ENABLED:
        return None
    
    if _SessionLocal is None:
        engine = get_engine()
        if engine:
            _SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )
    
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Get database session (dependency injection for FastAPI).
    
    Yields:
        SQLAlchemy session
    """
    if not DB_ENABLED:
        yield None
        return
    
    SessionLocal = get_session_factory()
    if not SessionLocal:
        yield None
        return
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Optional[Session], None, None]:
    """
    Get database session context manager.
    
    Yields:
        SQLAlchemy session or None if database is disabled
    """
    if not DB_ENABLED:
        yield None
        return
    
    SessionLocal = get_session_factory()
    if not SessionLocal:
        yield None
        return
    
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize database (create tables).
    
    This should be called on application startup.
    """
    if not DB_ENABLED:
        logger.info("Database disabled - using in-memory storage")
        return
    
    try:
        from .models import Base
        engine = get_engine()
        if engine:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


def close_db():
    """
    Close database connections.
    
    This should be called on application shutdown.
    """
    global _engine, _SessionLocal
    
    if _engine:
        try:
            _engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")
        finally:
            _engine = None
            _SessionLocal = None


def is_db_available() -> bool:
    """
    Check if database is available.
    
    Returns:
        True if database is enabled and accessible
    """
    if not DB_ENABLED:
        return False
    
    try:
        engine = get_engine()
        if not engine:
            return False
        
        # Try to connect
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.warning(f"Database not available: {e}")
        return False

