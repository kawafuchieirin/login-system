"""TODO models."""

from pydantic import BaseModel


class TodoCreate(BaseModel):
    title: str


class TodoUpdate(BaseModel):
    title: str | None = None
    completed: bool | None = None


class TodoResponse(BaseModel):
    todo_id: str
    title: str
    completed: bool
    created_at: str


class TodoListResponse(BaseModel):
    todos: list[TodoResponse]
