from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from app.config import settings
from app.models import Base
import logging

logger = logging.getLogger(__name__)

# Database engine configuration for GCP Cloud SQL
def create_database_engine():
    """Create SQLAlchemy engine with GCP Cloud SQL optimized settings."""
    if not settings.database_url:
        logger.warning("No database URL configured. Using SQLite for development.")
        return create_engine(
            "sqlite:///./testpilot.db",
            connect_args={"check_same_thread": False},
            echo=settings.debug
        )
    
    # GCP Cloud SQL PostgreSQL configuration
    engine = create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_size=10,  # Number of connections to maintain
        max_overflow=20,  # Additional connections that can be created
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=settings.debug
    )
    
    return engine

# Create engine instance
engine = create_database_engine()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables."""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def check_db_connection():
    """Check if database connection is working."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False 