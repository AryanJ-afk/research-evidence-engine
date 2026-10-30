import psycopg
from typing import Any
from fastapi import FastAPI, HTTPException, Query
from database import get_connection
from search import keyword_search

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


@app.get("/search")
def search_papers(q: str = Query(min_length=1, max_length=500), limit: int = Query(default=5, ge=1, le=20)) -> list[dict[str, Any]]:
    try:
        return keyword_search(q, limit)
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="Database Unavailable") from exc