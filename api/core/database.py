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
_connect_args = {"check_same_thread": False} if "sqlite" in _db_url else {}

if _db_url.startswith("postgresql+psycopg2://"):
    connect_timeout_s = int(os.getenv("DB_CONNECT_TIMEOUT", "5"))
    statement_timeout_ms = int(os.getenv("DB_STATEMENT_TIMEOUT_MS", "10000"))
    lock_timeout_ms = int(os.getenv("DB_LOCK_TIMEOUT_MS", "5000"))

    _connect_args["connect_timeout"] = connect_timeout_s

    options = []
    if statement_timeout_ms > 0:
        options.append(f"-c statement_timeout={statement_timeout_ms}")
    if lock_timeout_ms > 0:
        options.append(f"-c lock_timeout={lock_timeout_ms}")
    if options:
        _connect_args["options"] = " ".join(options)

engine = create_engine(_db_url, connect_args=_connect_args, pool_pre_ping=True)

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
