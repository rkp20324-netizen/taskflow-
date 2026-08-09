"""
SQLAlchemy ORM models — the three required tables:
users, projects, tasks — with the constraints and relationships
the brief asks for.
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)

    # A user can own many projects.
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="projects")
    # a_project.tasks resolves via this relationship.
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    # Closed set enforced at the Pydantic layer (schemas.py); the DB column
    # itself is a plain string so both real data and AI-parsed values fit.
    priority = Column(String, nullable=False, default="medium")
    # Intentionally plain TEXT (not Date) — holds either a manually entered
    # date string or an AI-parsed phrase like "next friday".
    due_date = Column(String, nullable=True)
    # todo / in_progress / done — used by the per-project stats endpoint.
    status = Column(String, nullable=False, default="todo")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # a_task.project resolves via this relationship.
    project = relationship("Project", back_populates="tasks")
