from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TodoItem(BaseModel):
    item: str
    details: Optional[str] = None
    created_by: str
    due_date: Optional[datetime] = None
    class Config:
        schema_extra = {
            "example": {
                "item": "Read the next chapter of the book",
                "details": "Chapter 5 about Python async programming",
                "created_by": "nikki",
                "due_date": "2026-06-25T10:00:00"
            }
        }

class Todo(TodoItem):
    id: int
    class Config:
        from_attributes = True