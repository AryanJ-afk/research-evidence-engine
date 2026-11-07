from fastapi import FastAPI
import logging
from pathlib import Path

import psycopg
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import get_connection
from app.search import router as search_router
from app.semantic_search import router as semantic_search_router
from app.ask import router as ask_router


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Research Evidence Engine",
    version="0.1.0",
)

app.include_router(search_router)
app.include_router(semantic_search_router)
app.include_router(ask_router)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)


@app.get("/", include_in_schema=False)
def root():
    return FileResponse(FRONTEND_DIR / "index.html")


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