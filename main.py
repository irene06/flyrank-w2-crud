import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar las variables de entorno del archivo .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Inicializar el cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(
    title="FlyRank Auth API",
    description="API con autenticación de Supabase y rutas protegidas",
    version="1.0.0"
)


# Esquema de seguridad para habilitar el candado en Swagger UI (/docs)
security = HTTPBearer()

# ==========================================
# 1. RUTA PÚBLICA
# ==========================================
@app.get("/public/info", tags=["Public"])
def public_info():
    """
    Endpoint público que no requiere autenticación.
    """
    return {
        "status": "success",
        "message": "Bienvenido a la API pública de FlyRank. Esta información es libre."
    }


# ==========================================
# 2. DEPENDENCIA DE SEGURIDAD (Validador de Token)
# ==========================================
def verify_supabase_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Valida el token Bearer utilizando la sesión de Supabase Auth.
    """
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado"
            )
        return user_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error de autenticación: {str(e)}"
        )


# ==========================================
# 3. RUTA PROTEGIDA
# ==========================================
@app.get("/protected/profile", tags=["Protected"])
def protected_profile(user = Depends(verify_supabase_token)):
    """
    Endpoint protegido que requiere un token de acceso válido de Supabase.
    """
    return {
        "status": "success",
        "message": "Acceso autorizado a la ruta protegida",
        "user_data": user
    }


# ==========================================
# 4. CIERRE DE SESIÓN (LOGOUT)
# ==========================================
@app.post("/auth/logout", tags=["Auth"])
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Cierra la sesión activa en Supabase utilizando el token Bearer.
    """
    token = credentials.credentials
    try:
        supabase.auth.sign_out(token)
        return {
            "status": "success",
            "message": "Sesión cerrada exitosamente"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo cerrar sesión: {str(e)}"
        )
# ==========================================
# 5. CONFIGURACIÓN DE POSTGRES Y CRUD DE TAREAS (A3)
# ==========================================
import psycopg
from pydantic import BaseModel

# Lee la URL de Postgres del .env
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgres://postgres:dev@localhost:5432/tasks"
)


def get_db_connection():
  return psycopg.connect(DATABASE_URL)


# Inicializar la tabla y datos de ejemplo si está vacía al arrancar
def init_db():
  try:
    with get_db_connection() as conn:
      with conn.cursor() as cur:
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        done BOOLEAN NOT NULL DEFAULT FALSE
                    );
                """)
        cur.execute("SELECT COUNT(*) FROM tasks;")
        count = cur.fetchone()[0]
        if count == 0:
          cur.executemany(
              "INSERT INTO tasks (title, done) VALUES (%s, %s);",
              [
                  ("Aprender Docker", False),
                  ("Configurar PostgreSQL", True),
                  ("Completar la tarea A3", False),
              ],
          )
        conn.commit()
  except Exception as e:
    print(
        "Aviso: No se pudo conectar a Postgres al iniciar (puede que el"
        f" contenedor aún no esté activo): {e}"
    )


# inicializar la app
init_db()


# Modelo Pydantic para las tareas
class TaskCreate(BaseModel):
  title: str
  done: bool = False


class TaskUpdate(BaseModel):
  title: str
  done: bool


# --- ENDPOINTS DE TAREAS (CRUD) ---


@app.get("/tasks", tags=["Tasks"])
def get_tasks():
  """Lista todas las tareas desde PostgreSQL."""
  with get_db_connection() as conn:
    with conn.cursor() as cur:
      cur.execute("SELECT id, title, done FROM tasks ORDER BY id;")
      rows = cur.fetchall()
      tasks = [{"id": row[0], "title": row[1], "done": row[2]} for row in rows]
      return tasks


@app.get("/tasks/{task_id}", tags=["Tasks"])
def get_task(task_id: int):
  """Obtiene una tarea por su ID usando consultas."""
  with get_db_connection() as conn:
    with conn.cursor() as cur:
      cur.execute(
          "SELECT id, title, done FROM tasks WHERE id = %s;", (task_id,)
      )
      row = cur.fetchone()
      if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Task not found"},
        )
      return {"id": row[0], "title": row[1], "done": row[2]}


@app.post("/tasks", status_code=status.HTTP_201_CREATED, tags=["Tasks"])
def create_task(task: TaskCreate):
  """Crea una nueva tarea en Postgres usando RETURNING."""
  if not task.title.strip():
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"error": "Title cannot be empty"},
    )
  with get_db_connection() as conn:
    with conn.cursor() as cur:
      cur.execute(
          "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title,"
          " done;",
          (task.title, task.done),
      )
      row = cur.fetchone()
      conn.commit()
      return {"id": row[0], "title": row[1], "done": row[2]}


@app.put("/tasks/{task_id}", tags=["Tasks"])
def update_task(task_id: int, task: TaskUpdate):
  """Actualiza una tarea existente."""
  with get_db_connection() as conn:
    with conn.cursor() as cur:
      cur.execute(
          "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id,"
          " title, done;",
          (task.title, task.done, task_id),
      )
      row = cur.fetchone()
      conn.commit()
      if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Task not found"},
        )
      return {"id": row[0], "title": row[1], "done": row[2]}


@app.delete(
    "/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tasks"]
)
def delete_task(task_id: int):
  """Elimina una tarea por su ID."""
  with get_db_connection() as conn:
    with conn.cursor() as cur:
      cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id;", (task_id,))
      row = cur.fetchone()
      conn.commit()
      if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Task not found"},
        )
      return