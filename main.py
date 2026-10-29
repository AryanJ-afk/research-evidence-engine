import psycopg
from fastapi import FastAPI, HTTPException
from database import get_connection

app = FastAPI(title="Research Evidence Enginer")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/health/db")
def database_health() -> dict[str, bool]:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
    except psycopg.Error as exe:
        raise HTTPException(status_code=503, detail="Database Unavailable") from exe
    
    return {"connected": result == (1,)}