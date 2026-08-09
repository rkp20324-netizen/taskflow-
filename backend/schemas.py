"""
Pydantic request/response models.

Includes the required Field constraint (priority restricted to the closed
"low" / "medium" / "high" set) and a custom validator (title must not be
blank after trimming whitespace).
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict

Priority = Literal["low", "medium", "high"]
Status = Literal["todo", "in_progress", "done"]


# ---------- Users ----------

class UserCreate(BaseModel):
    name: str
    email: str

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v


class UserOut(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


# ---------- Projects ----------

class ProjectCreate(BaseModel):
    name: str
    owner_id: int

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v


class ProjectOut(BaseModel):
    id: int
    name: str
    owner_id: int

    model_config = ConfigDict(from_attributes=True)


# ---------- Tasks ----------

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    # Field constraint: priority is restricted to the closed 3-value set.
    priority: Priority = Field(default="medium")
    due_date: Optional[str] = None
    status: Status = Field(default="todo")
    project_id: int

    # Custom validator: reject a blank title after trimming whitespace.
    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be blank")
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    due_date: Optional[str] = None
    status: Optional[Status] = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("title must not be blank")
        return v


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    priority: Priority
    due_date: Optional[str] = None
    status: Status
    project_id: int

    model_config = ConfigDict(from_attributes=True)


# ---------- Stats ----------

class ProjectStats(BaseModel):
    project_id: int
    project_name: str
    task_count: int
    by_status: dict


# ---------- AI Quick-Add ----------

class QuickAddRequest(BaseModel):
    description: str
    project_id: int

    @field_validator("description")
    @classmethod
    def description_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("description must not be blank")
        return v
