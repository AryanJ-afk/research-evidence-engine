from fastapi import FastAPI
import logging

import psycopg
from fastapi.responses import JSONResponse

from app.database import get_connection
from app.search import router as search_router
from app.semantic_search import router as semantic_search_router


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Research Evidence Engine",
    version="0.1.0",
)

app.include_router(search_router)
app.include_router(semantic_search_router)

@app.get("/")
def root():
    return {
        "message": "Welcome to Research Evidence Engine"
    }


@app.get("/health")
def health():
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1").fetchone()

    except psycopg.Error:
        logger.exception("Database health check failed")

        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "api": "ok",
                "database": "unavailable",
            },
            headers={"Cache-Control": "no-store"},
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "api": "ok",
            "database": "ok",
        },
        headers={"Cache-Control": "no-store"},
    )