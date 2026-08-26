import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from supabase import Client, create_client

# 1. Cargar variables de entorno y crear cliente de Supabase
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Inicializar FastAPI
app = FastAPI()


# 3. Ruta de prueba para verificar que el servidor responde
@app.get("/")
def home():
  return {"mensaje": "¡El servidor está vivo!"}


# 4. Modelo de datos para autenticación
class AuthCredentials(BaseModel):
  email: str
  password: str


# 5. Endpoints de Registro y Login
@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def sign_up(credentials: AuthCredentials):
  if not credentials.email or not credentials.password:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"error": "Email and password are required"},
    )
  try:
    response = supabase.auth.sign_up({
        "email": credentials.email,
        "password": credentials.password,
    })
    return {"message": "User registered successfully", "user": response.user}
  except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail={"error": str(e)}
    )


@app.post("/auth/login", status_code=status.HTTP_200_OK)
def log_in(credentials: AuthCredentials):
  if not credentials.email or not credentials.password:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"error": "Email and password are required"},
    )
  try:
    response = supabase.auth.sign_in_with_password({
        "email": credentials.email,
        "password": credentials.password,
    })
    return {
        "access_token": response.session.access_token,
        "refresh_token": response.session.refresh_token,
    }
  except Exception:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "Invalid login credentials"},
    )