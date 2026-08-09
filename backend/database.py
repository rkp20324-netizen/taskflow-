"""
Database setup: SQLAlchemy engine, session factory, declarative base,
and the shared get_db() dependency reused across the whole backend
(Section 1 CRUD, Section 2 sort/search, Section 3 quick-add).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite file lives alongside the backend package. Easy to inspect / reset.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "taskflow.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# check_same_thread=False is required for SQLite when used with FastAPI's
# threaded request handling.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Shared DB-session dependency (FastAPI Depends).
    Reused across every endpoint in main.py that touches the database,
    including the Section 2 (sort/search) and Section 3 (quick-add)
    endpoints added to this same backend.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
