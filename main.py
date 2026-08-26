from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import sqlite3

app = FastAPI()

DB_NAME = "tasks.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por nombre
    return conn

# Inicializar la base de datos y sembrar datos si está vacía (Etapa 0)
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL CHECK (done IN (0, 1))
        )
    """)
    
    # Verificar si está vacía para sembrar los 3 ejemplos
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    if count == 0:
        initial_tasks = [
            ("Aprender FastAPI", 0),
            ("Completar Stage 2", 0),
            ("Subir a GitHub", 1),
        ]
        cursor.executemany("INSERT INTO tasks (title, done) VALUES (?, ?)", initial_tasks)
        conn.commit()
    
    conn.close()

# Ejecutar la inicialización al arrancar
init_db()

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

# GET /tasks (Etapa 1)
@app.get("/tasks")
def get_tasks():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks")
    rows = cursor.fetchall()
    conn.close()
    
    return [{"id": row["id"], "title": row["title"], "done": bool(row["done"])} for row in rows]

# GET /tasks/{task_id} (Etapa 1)
@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

# POST /tasks (Etapa 2)
@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (task.title, 0))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    
    return {"id": new_id, "title": task.title, "done": False}

# PUT /tasks/{task_id} (Etapa 3)
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_data: TaskUpdate):
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar si existe
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    current_title = row["title"]
    current_done = row["done"]
    
    new_title = task_data.title if task_data.title is not None else current_title
    new_done = int(task_data.done) if task_data.done is not None else current_done
    
    cursor.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?", (new_title, new_done, task_id))
    conn.commit()
    conn.close()
    
    return {"id": task_id, "title": new_title, "done": bool(new_done)}

# DELETE /tasks/{task_id} (Etapa 3)
@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    cursor.execute("DELETE FROM tasks WHERE id = ?_?", (task_id,)) # (O simplemente id = ?)
    # Corrección limpia:
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return None