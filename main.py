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