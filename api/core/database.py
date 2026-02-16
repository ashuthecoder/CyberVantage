"""
Database configuration and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from api.core.config import settings

# Normalise the database URL so SQLAlchemy can use it with psycopg2
_db_url = settings.DATABASE_URL
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
if _db_url.startswith("postgresql+psycopg2://") and "sslmode=" not in _db_url:
    _sslmode = os.getenv("POSTGRES_SSLMODE", "require")
    _sep = "&" if "?" in _db_url else "?"
    _db_url = f"{_db_url}{_sep}sslmode={_sslmode}"

# Create engine
engine = create_engine(
    _db_url,
    connect_args={"check_same_thread": False} if "sqlite" in _db_url else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
