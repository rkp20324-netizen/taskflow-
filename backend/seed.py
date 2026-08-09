"""
Seeds the real TaskFlow database with a user, a project, and N tasks.
Used to produce realistic-size snapshots for the Section 2 benchmark.

Usage:
    python3 seed.py <num_tasks>

Example:
    python3 seed.py 10
    python3 seed.py 500
    python3 seed.py 3000
"""
import sys
import random

from database import Base, engine, SessionLocal
import models

PRIORITIES = ["low", "medium", "high"]
STATUSES = ["todo", "in_progress", "done"]


def seed(num_tasks: int):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == "seed@taskflow.local").first()
        if not user:
            user = models.User(name="Seed User", email="seed@taskflow.local")
            db.add(user)
            db.commit()
            db.refresh(user)

        project = models.Project(name=f"Seed Project ({num_tasks} tasks)", owner_id=user.id)
        db.add(project)
        db.commit()
        db.refresh(project)

        for i in range(num_tasks):
            task = models.Task(
                title=f"Seed task {i} {random.randint(1000, 9999)}",
                priority=random.choice(PRIORITIES),
                due_date=random.choice([None, "tomorrow", "next friday", "2026-09-01"]),
                status=random.choice(STATUSES),
                project_id=project.id,
            )
            db.add(task)
        db.commit()
        print(f"Seeded {num_tasks} tasks into project_id={project.id} (owner user_id={user.id})")
    finally:
        db.close()


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    seed(n)
