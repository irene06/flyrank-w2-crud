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
    
    # 2. Crea el nuevo ID (el último id + 1)
    new_id = tasks[-1]["id"] + 1 if tasks else 1
    
    # 3. Crea el objeto
    new_task = {"id": new_id, "title": task.title, "done": False}
    
    # 4. Guardar
    tasks.append(new_task)
    
    return new_task
# 1.  actualizaciones
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

# 2. Endpoint DELETE
@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(index)
            return None # 204 no devuelve contenido
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

# 3. Endpoint para PUT (Actualizar)
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_data: TaskUpdate):
    for task in tasks:
        if task["id"] == task_id:
            # campos que vienen del JSON
            if task_data.title is not None:
                task["title"] = task_data.title
            if task_data.done is not None:
                task["done"] = task_data.done
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")