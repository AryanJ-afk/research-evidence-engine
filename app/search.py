from typing import Any
from psycopg.rows import dict_row
from app.database import get_connection


def keyword_search(query: str, limit: int = 5) -> list[dict[str, Any]]:
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    arxiv_id, title, abstract,
                    ts_rank_cd(
                        to_tsvector('english', title || ' ' || abstract),
                        websearch_to_tsquery('english', %(query)s)
                    ) AS score
                FROM papers
                WHERE
                    to_tsvector('english', title || ' ' || abstract)
                    @@ websearch_to_tsquery('english', %(query)s)
                ORDER BY score DESC, arxiv_id
                LIMIT %(limit)s
                """,
                {"query": query, "limit": limit},
            )
            return cursor.fetchall()