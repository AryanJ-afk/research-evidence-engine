from fastapi import FastAPI
from database import get_connection

app = FastAPI(title="Research Evidence Enginer")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/health/db")
def database_health() -> dict[str, bool]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
    
    return {"connected": result == (1,)}