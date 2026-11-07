import logging
from time import perf_counter

import psycopg
from fastapi import APIRouter, HTTPException, Query
from psycopg.rows import dict_row

from app.database import get_connection


logger = logging.getLogger(__name__)

router = APIRouter(tags=["search"])

SEARCH_SQL = """
SELECT
    p.arxiv_id,
    p.title,
    p.abstract,
    p.authors,
    p.categories,
    p.source_updated_on,
    ts_rank(
        to_tsvector('english', p.title || ' ' || p.abstract),
        query.terms
    ) AS score
FROM papers AS p
CROSS JOIN (
    SELECT plainto_tsquery('english', %s) AS terms
) AS query
WHERE
    to_tsvector('english', p.title || ' ' || p.abstract)
    @@ query.terms
ORDER BY score DESC, p.arxiv_id ASC
LIMIT %s;
"""


@router.get("/search")
def search_papers(
    q: str = Query(min_length=1, max_length=300),
    limit: int = Query(default=10, ge=1, le=50),
):
    query_text = q.strip()

    if not query_text:
        raise HTTPException(
            status_code=422,
            detail="Search query must contain non-whitespace characters.",
        )

    started_at = perf_counter()

    try:
        with get_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(SEARCH_SQL, (query_text, limit))
                papers = cursor.fetchall()

    except psycopg.errors.QueryCanceled:
        logger.exception("Search query was canceled")
        raise HTTPException(
            status_code=504,
            detail="Search exceeded its execution time limit.",
        ) from None

    except psycopg.OperationalError:
        logger.exception("Database connection failed during search")
        raise HTTPException(
            status_code=503,
            detail="Search is temporarily unavailable.",
        ) from None

    except psycopg.Error:
        logger.exception("Database error during search")
        raise HTTPException(
            status_code=500,
            detail="Search failed.",
        ) from None

    retrieval_ms = round((perf_counter() - started_at) * 1000, 2)

    for paper in papers:
        paper["url"] = f"https://arxiv.org/abs/{paper['arxiv_id']}"

    return {
        "query": query_text,
        "limit": limit,
        "returned": len(papers),
        "retrieval_ms": retrieval_ms,
        "papers": papers,
    }