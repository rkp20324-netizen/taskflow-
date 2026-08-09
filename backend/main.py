"""
TaskFlow backend — one FastAPI app serving all three graded sections:
  Section 1: relational CRUD + stats + middleware + CORS
  Section 2: sort/search endpoints powered by algorithms.py
  Section 3: /tasks/quick-add powered by ai_parser.py
"""
import time
import logging
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import ValidationError

from database import Base, engine, get_db
import models
import schemas
from algorithms import insertion_sort, binary_search, linear_search
from ai_parser import parse_task

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("taskflow")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TaskFlow API")

# ---------------------------------------------------------------------------
# Task 8: custom middleware — logs method, path, processing time (ms) for
# every request.
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(f"{request.method} {request.url.path} - {duration_ms:.2f}ms")
    return response


# ---------------------------------------------------------------------------
# Task 9: CORS — explicit origin(s), explicit methods, explicit headers.
# Adjust ALLOWED_ORIGINS if your static server runs on a different port.
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
@app.post("/users", response_model=schemas.UserOut, status_code=201)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=422, detail="email already registered")
    db_user = models.User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users", response_model=List[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
@app.post("/projects", response_model=schemas.ProjectOut, status_code=201)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    owner = db.query(models.User).filter(models.User.id == project.owner_id).first()
    if not owner:
        raise HTTPException(status_code=422, detail="owner_id does not reference an existing user")
    db_project = models.Project(name=project.name, owner_id=project.owner_id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.get("/projects", response_model=List[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()


# ---------------------------------------------------------------------------
# Task 6: per-project stats — SQL aggregate (COUNT + GROUP BY) via SQLAlchemy,
# not computed in Python after fetching every row.
# ---------------------------------------------------------------------------
@app.get("/projects/{project_id}/stats", response_model=schemas.ProjectStats)
def project_stats(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="project not found")

    total = (
        db.query(func.count(models.Task.id))
        .filter(models.Task.project_id == project_id)
        .scalar()
    )

    rows = (
        db.query(models.Task.status, func.count(models.Task.id))
        .join(models.Project, models.Task.project_id == models.Project.id)
        .filter(models.Project.id == project_id)
        .group_by(models.Task.status)
        .all()
    )
    by_status = {status: count for status, count in rows}

    return schemas.ProjectStats(
        project_id=project.id,
        project_name=project.name,
        task_count=total or 0,
        by_status=by_status,
    )


# ---------------------------------------------------------------------------
# Tasks — CRUD
# ---------------------------------------------------------------------------
def _get_task_or_404(task_id: int, db: Session) -> models.Task:
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@app.post("/tasks", response_model=schemas.TaskOut, status_code=201)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=422, detail="project_id does not reference an existing project")
    db_task = models.Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


# NOTE: this basic list endpoint stays separate from the Section 2
# sort-powered endpoint below (?sort=...) so the plain CRUD "list" path
# is unaffected by the custom sort/search engine.
@app.get("/tasks", response_model=List[schemas.TaskOut])
def list_tasks(
    project_id: Optional[int] = None,
    sort: Optional[str] = Query(default=None, description="priority | due_date"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Task)
    if project_id is not None:
        query = query.filter(models.Task.project_id == project_id)
    tasks = query.all()

    if sort is None:
        return tasks

    # -----------------------------------------------------------------
    # Section 2 Task 4: GET /tasks?sort=priority|due_date is powered by
    # our own insertion_sort, not the DB's ORDER BY and not Python's
    # built-in sort.
    # -----------------------------------------------------------------
    records = [schemas.TaskOut.model_validate(t).model_dump() for t in tasks]

    if sort == "priority":
        rank = {"low": 1, "medium": 2, "high": 3}
        for r in records:
            r["_sort_key"] = rank.get(r["priority"], 0)
        insertion_sort(records, "_sort_key")
        for r in records:
            del r["_sort_key"]
    elif sort == "due_date":
        for r in records:
            r["_sort_key"] = r["due_date"] or ""
        insertion_sort(records, "_sort_key")
        for r in records:
            del r["_sort_key"]
    else:
        raise HTTPException(status_code=422, detail="sort must be 'priority' or 'due_date'")

    return records


# -----------------------------------------------------------------------
# Section 2 Task 4: GET /tasks/search?title=...&algo=binary|linear
# Declared BEFORE /tasks/{task_id} so "search" isn't swallowed as an id.
# -----------------------------------------------------------------------
@app.get("/tasks/search", response_model=schemas.TaskOut)
def search_tasks(
    title: str,
    algo: str = Query(default="binary", pattern="^(binary|linear)$"),
    db: Session = Depends(get_db),
):
    tasks = db.query(models.Task).all()
    index = [{"id": t.id, "title": t.title} for t in tasks]

    if algo == "binary":
        insertion_sort(index, "title")
        found_at = binary_search(index, title, "title")
    else:
        found_at = linear_search(index, title, "title")

    if found_at == -1:
        raise HTTPException(status_code=404, detail="no task with that exact title")

    matched_id = index[found_at]["id"]
    task = _get_task_or_404(matched_id, db)
    return task


@app.get("/tasks/{task_id}", response_model=schemas.TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    return _get_task_or_404(task_id, db)


@app.put("/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    db_task = _get_task_or_404(task_id, db)
    updates = task.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(db_task, field, value)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/tasks/{task_id}", status_code=200)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = _get_task_or_404(task_id, db)
    db.delete(db_task)
    db.commit()
    return {"deleted": True, "id": task_id}


# ---------------------------------------------------------------------------
# Section 3: AI Quick-Add
# ---------------------------------------------------------------------------
@app.post("/tasks/quick-add", response_model=schemas.TaskOut, status_code=201)
def quick_add_task(payload: schemas.QuickAddRequest, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=422, detail="project_id does not reference an existing project")

    # Role-based "prompt" structure kept even though the mock answers it —
    # this is what a real LLM call would be built from.
    system_message = {
        "role": "system",
        "content": (
            "You are a task-parsing assistant. Extract title, priority "
            "(low/medium/high) and a due_date_hint phrase from the user's "
            "free-text task description."
        ),
    }
    user_message = {"role": "user", "content": payload.description}
    _messages = [system_message, user_message]  # would be sent to a real LLM

    parsed = parse_task(payload.description)

    try:
        task_data = schemas.TaskCreate(
            title=parsed["title"],
            priority=parsed["priority"],
            due_date=parsed["due_date_hint"],
            project_id=payload.project_id,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    db_task = models.Task(**task_data.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.get("/")
def root():
    return {"service": "TaskFlow API", "docs": "/docs"}
