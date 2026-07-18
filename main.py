from fastapi import FastAPI

app = FastAPI()

# Etapa 0: Tu endpoint inicial
@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

# Etapa 1: Endpoint de salud (Health check)
@app.get("/health")
def read_health():
    return {"status": "ok"}