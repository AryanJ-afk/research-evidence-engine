import json
import logging
from functools import lru_cache
from time import perf_counter

import psycopg
from fastapi import APIRouter, HTTPException, Query
from langchain_openai import OpenAIEmbeddings
from openai import APIError, APITimeoutError, RateLimitError
from psycopg.rows import dict_row

from app.database import get_connection


logger = logging.getLogger(__name__)
router = APIRouter(tags=["search"])

MODEL = "text-embedding-3-small"
DIMENSIONS = 1536

SEMANTIC_SEARCH_SQL = """
SELECT
    p.arxiv_id,
    p.title,
    p.abstract,
    p.authors,
    p.categories,
    p.source_updated_on,
    1 - (e.embedding <=> query.embedding) AS score
FROM paper_embeddings AS e
JOIN papers AS p ON p.arxiv_id = e.arxiv_id
CROSS JOIN (
    SELECT %s::vector AS embedding
) AS query
WHERE e.embedding_model = %s
ORDER BY
    e.embedding <=> query.embedding,
    p.arxiv_id
LIMIT %s;
"""


@lru_cache(maxsize=1)
def get_embedding_client():
    return OpenAIEmbeddings(
        model=MODEL,
        dimensions=DIMENSIONS,
        request_timeout=30,
        max_retries=1,
        check_embedding_ctx_length=False,
    )


def retrieve_semantic(q: str, limit: int):
    query_text = q.strip()

    if not query_text:
        raise HTTPException(
            status_code=422,
            detail="Search query must contain non-whitespace characters.",
        )

    embedding_started = perf_counter()

    try:
        query_vector = get_embedding_client().embed_query(query_text)

    except APITimeoutError:
        logger.exception("Query embedding timed out")
        raise HTTPException(
            status_code=504,
            detail="The embedding service timed out.",
        ) from None

    except RateLimitError:
        logger.exception("Embedding API rate or quota limit reached")
        raise HTTPException(
            status_code=503,
            detail="The embedding service is currently unavailable.",
        ) from None

    except APIError:
        logger.exception("Embedding API request failed")
        raise HTTPException(
            status_code=502,
            detail="Could not generate the query embedding.",
        ) from None

    embedding_ms = (perf_counter() - embedding_started) * 1000

    if len(query_vector) != DIMENSIONS:
        raise HTTPException(
            status_code=502,
            detail="The embedding service returned unexpected dimensions.",
        )

    retrieval_started = perf_counter()

    try:
        with get_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    SEMANTIC_SEARCH_SQL,
                    (
                        json.dumps(query_vector, allow_nan=False),
                        MODEL,
                        limit,
                    ),
                )
                papers = cursor.fetchall()

    except psycopg.errors.QueryCanceled:
        logger.exception("Semantic search query timed out")
        raise HTTPException(
            status_code=504,
            detail="Semantic search exceeded its execution time limit.",
        ) from None

    except psycopg.OperationalError:
        logger.exception("Database connection failed during semantic search")
        raise HTTPException(
            status_code=503,
            detail="Search is temporarily unavailable.",
        ) from None

    except psycopg.Error:
        logger.exception("Database error during semantic search")
        raise HTTPException(
            status_code=500,
            detail="Semantic search failed.",
        ) from None

    retrieval_ms = (perf_counter() - retrieval_started) * 1000

    for paper in papers:
        paper["url"] = f"https://arxiv.org/abs/{paper['arxiv_id']}"

    return {
        "query": query_text,
        "search_type": "semantic",
        "embedding_model": MODEL,
        "score_type": "cosine_similarity",
        "limit": limit,
        "returned": len(papers),
        "embedding_ms": round(embedding_ms, 2),
        "retrieval_ms": round(retrieval_ms, 2),
        "papers": papers,
    }
    
    
@router.get("/search/semantic")
def semantic_search(
    q: str = Query(min_length=1, max_length=300),
    limit: int = Query(default=10, ge=1, le=50),
):
    return retrieve_semantic(q=q, limit=limit)