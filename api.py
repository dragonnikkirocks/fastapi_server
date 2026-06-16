from fastapi import APIRouter,FastAPI,Path,HTTPException
from model import Todo,TodoItem

router = APIRouter()
app = FastAPI()
todo_list = []

@router.get("/")
async def welcome() -> dict:
    return {"message": "Hello noah.}"}

@router.post("/todo", status_code=201, responses={
    400: {"description": "Todo list is full"}
})
async def add_todos(todo: Todo) -> dict:
    if len(todo_list) < 2:
        todo_list.append(todo)
        print("todo list size ", len(todo_list))
        return {"message": "Task added to list."}
    else:
        raise HTTPException(status_code=400, detail="Todo list is full. Task not added to list.")
                

@router.get("/todo")
async def get_todolist() -> dict:
    if len(todo_list)== 0:
        return {"ERROR ": "todo list is empty"}
    else:
        return {"todo list ": todo_list}

@router.get("/todo/{todo_id}")
async def get_single_todo(todo_id: int = Path(..., title="The ID of the todo to retrieve.")) -> dict:
    for todo in todo_list:
        if todo.id == todo_id:
            return {"todo": todo}
    return {"message": "Todo with supplied ID doesn't exist."}


@router.put("/todo/{todo_id}")
async def update_todo(todo_data: TodoItem, todo_id: int = Path(..., title="The ID of the todo to be updated")) -> dict:
    for todo in todo_list:
        if todo.id == todo_id:
            todo.item = todo_data.item
            return {"message": "Todo updated successfully."}
    return {"message": "Todo with supplied ID doesn't exist."}

@router.delete("/todo/{todo_id}")
async def delete_todo(todo_data:TodoItem, todo_id =Path(...,title= "ID of todo that needs to be deleted")):
    for todo in todo_list:
        if todo.id ==todo_id:
            todo.item = todo_data.item
            return {"message": "Todo deleted successfully."}
    return {"message": "Todo with supplied ID doesn't exist."}

@router.delete("todo")
async def delete_all() ->dict:
    todo_list.clear()
    return {"message": "Todos deleted successfully."}

app.include_router(router)