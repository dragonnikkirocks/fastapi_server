from fastapi import APIRouter, FastAPI, Path, HTTPException, Request, Form, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from model import Todo, TodoItem
from datetime import datetime

router = APIRouter()
app = FastAPI()
templates = Jinja2Templates(directory="templates")
todo_list = []

@router.get("/", response_class=HTMLResponse)
async def welcome(request: Request):
    sorted_todos = sorted(todo_list, key=lambda x: x.due_date if x.due_date else datetime.max)
    return templates.TemplateResponse("index.html", {"request": request, "todos": sorted_todos})

@router.post(
    "/todo",
    status_code=status.HTTP_201_CREATED,
    response_model=Todo,
    responses={400: {"description": "Todo list is full"}},
)
async def add_todos(todo: Todo) -> Todo:
    if len(todo_list) >= 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Todo list is full. Task not added to list.",
        )
    todo_list.append(todo)
    return todo

@router.post("/todo/form")
async def add_todo_form(
    request: Request,
    id: int = Form(...),
    item: str = Form(...),
    created_by: str = Form(...),
    details: str = Form(default=""),
    due_date: str = Form(default=None),
):
    if len(todo_list) >= 2:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "todos": todo_list,
                "error": "Todo list is full.",
            },
        )

    from datetime import datetime
    parsed_due_date = None
    if due_date:
        try:
            parsed_due_date = datetime.fromisoformat(due_date)
        except ValueError:
            parsed_due_date = None

    todo = Todo(
        id=id, 
        item=item, 
        created_by=created_by,
        details=details if details else None,
        due_date=parsed_due_date
    )
    todo_list.append(todo)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/todo", response_model=list[Todo])
async def get_todolist() -> list[Todo]:
    if not todo_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo list is empty.")
    sorted_todos = sorted(todo_list, key=lambda x: x.due_date if x.due_date else datetime.max)
    return sorted_todos

@router.get("/todo/{todo_id}", response_model=list[Todo])
async def get_single_todo(
    todo_id: int = Path(..., title="The ID of the todo to retrieve.")
) -> list[Todo]:
    matches = [todo for todo in todo_list if todo.id == todo_id]
    if not matches:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo with supplied ID doesn't exist.")
    return matches

@router.put("/todo/{todo_id}", response_model=Todo)
async def update_todo(
    todo_data: TodoItem,
    todo_id: int = Path(..., title="The ID of the todo to be updated"),
) -> Todo:
    for todo in todo_list:
        if todo.id == todo_id:
            todo.item = todo_data.item
            todo.details = todo_data.details
            todo.created_by = todo_data.created_by
            todo.due_date = todo_data.due_date
            return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo with supplied ID doesn't exist.")

@router.delete("/todo/{todo_id}", response_model=Todo)
async def delete_todo(
    todo_id: int = Path(..., title="ID of todo that needs to be deleted")
) -> Todo:
    for todo in todo_list:
        if todo.id == todo_id:
            todo_list.remove(todo)
            return todo
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Todo with supplied ID doesn't exist.",
    )

@router.post("/todo/{todo_id}")
async def delete_todo_form(
    request: Request,
    todo_id: int = Path(..., title="ID of todo that needs to be deleted")
):
    for todo in todo_list:
        if todo.id == todo_id:
            todo_list.remove(todo)
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@router.delete("/todo")
async def delete_all() -> dict:
    todo_list.clear()
    return {"message": "Todos deleted successfully."}

app.include_router(router)