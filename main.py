from fastapi import FastAPI, HTTPException

app = FastAPI()

# Tu lista en memoria (Etapa 2)
tasks = [
    {"id": 1, "title": "Aprender FastAPI", "done": False},
    {"id": 2, "title": "Completar Stage 2", "done": False},
    {"id": 3, "title": "Subir a GitHub", "done": True},
]

@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def read_health():
    return {"status": "ok"}

# GET /tasks (lista todo)
@app.get("/tasks")
def get_tasks():
    return tasks

# GET /tasks/{id} (busca una tarea)
@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    # Si no se encuentra el ID, devuelve not found
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")