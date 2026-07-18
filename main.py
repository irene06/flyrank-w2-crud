from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Modelo para validar lo que el cliente envía
class TaskCreate(BaseModel):
    title: str

# Tu lista en memoria
tasks = [
    {"id": 1, "title": "Aprender FastAPI", "done": False},
    {"id": 2, "title": "Completar Stage 2", "done": False},
    {"id": 3, "title": "Subir a GitHub", "done": True},
]

# ... / , /health, /tasks, /tasks/{id})

# ETAPA 3: POST /tasks
@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    # 1. 
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    # 2. Crear el nuevo ID (el último id + 1)
    new_id = tasks[-1]["id"] + 1 if tasks else 1
    
    # 3. Crear el objeto
    new_task = {"id": new_id, "title": task.title, "done": False}
    
    # 4. Guardar
    tasks.append(new_task)
    
    return new_task