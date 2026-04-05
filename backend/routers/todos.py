"""TODO router."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from dependencies import get_current_user
from models.todo import TodoCreate, TodoListResponse, TodoResponse, TodoUpdate
from services.todo_service import create_todo, delete_todo, list_todos, update_todo

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("", response_model=TodoListResponse)
def get_todos(user_id: str = Depends(get_current_user)) -> TodoListResponse:
    todos = list_todos(user_id)
    return TodoListResponse(todos=[TodoResponse(**t) for t in todos])


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def post_todo(request: TodoCreate, user_id: str = Depends(get_current_user)) -> TodoResponse:
    todo = create_todo(user_id, request.title)
    return TodoResponse(**todo)


@router.patch("/{todo_id}", response_model=TodoResponse)
def patch_todo(todo_id: str, request: TodoUpdate, user_id: str = Depends(get_current_user)) -> TodoResponse:
    todo = update_todo(user_id, todo_id, title=request.title, completed=request.completed)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return TodoResponse(**todo)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_todo(todo_id: str, user_id: str = Depends(get_current_user)) -> Response:
    if not delete_todo(user_id, todo_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
