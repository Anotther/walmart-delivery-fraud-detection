"""
Database connection and session management.
Provides SQLAlchemy engine and session factory.
"""
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from src.config.settings import DATABASE_URL, DEBUG

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=DEBUG,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


@contextmanager
def get_session():
    """
    Context manager for database sessions.
    Automatically handles commit/rollback and closing.

    Usage:
        with get_session() as session:
            session.query(...)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_connection():
    """
    Get a raw database connection for direct SQL execution.

    Usage:
        with get_connection() as conn:
            conn.execute(text("SELECT * FROM orders"))
    """
    return engine.connect()


def test_connection() -> bool:
    """Test if database connection is working."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


def create_all_tables():
    """Create all tables defined in ORM models."""
    Base.metadata.create_all(bind=engine)


def drop_all_tables():
    """Drop all tables. Use with caution!"""
    Base.metadata.drop_all(bind=engine)
