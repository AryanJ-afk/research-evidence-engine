import argparse
import json
from time import perf_counter

import tiktoken
from langchain_openai import OpenAIEmbeddings

from app.database import get_connection


MODEL = "text-embedding-3-small"
DIMENSIONS = 1536
BATCH_SIZE = 25
MAX_INPUT_TOKENS = 8000

SELECT_PENDING_SQL = """
SELECT p.arxiv_id, p.title, p.abstract
FROM papers AS p
LEFT JOIN paper_embeddings AS e
    ON e.arxiv_id = p.arxiv_id
WHERE
    p.arxiv_id > %s
    AND (
        e.arxiv_id IS NULL
        OR e.embedding_model <> %s
    )
ORDER BY p.arxiv_id
LIMIT %s;
"""

SAVE_SQL = """
INSERT INTO paper_embeddings (
    arxiv_id,
    embedding_model,
    embedding
)
VALUES (%s, %s, %s::vector)
ON CONFLICT (arxiv_id) DO UPDATE SET
    embedding_model = EXCLUDED.embedding_model,
    embedding = EXCLUDED.embedding,
    embedded_at = CURRENT_TIMESTAMP;
"""


def prepare_texts(papers, encoding):
    texts = []

    for arxiv_id, title, abstract in papers:
        text = f"{title.strip()}\n\n{abstract.strip()}"
        token_count = len(
            encoding.encode(text, disallowed_special=())
        )

        if token_count > MAX_INPUT_TOKENS:
            raise ValueError(
                f"Paper {arxiv_id} has {token_count} tokens; "
                f"our limit is {MAX_INPUT_TOKENS}. "
                "Handle this paper before continuing."
            )

        texts.append(text)

    return texts


def save_batch(connection, papers, vectors):
    if len(vectors) != len(papers):
        raise ValueError("The number of embeddings does not match the papers")

    rows = []

    for paper, vector in zip(papers, vectors):
        if len(vector) != DIMENSIONS:
            raise ValueError("Unexpected embedding dimensions")

        rows.append((
            paper[0],
            MODEL,
            json.dumps(vector, allow_nan=False),
        ))

    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.executemany(SAVE_SQL, rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be positive")

    encoding = tiktoken.encoding_for_model(MODEL)

    embeddings = OpenAIEmbeddings(
        model=MODEL,
        dimensions=DIMENSIONS,
        chunk_size=BATCH_SIZE,
        check_embedding_ctx_length=False,
        request_timeout=30,
        max_retries=2,
    )

    processed = 0
    last_id = ""
    started_at = perf_counter()

    with get_connection() as connection:
        while processed < args.limit:
            batch_limit = min(BATCH_SIZE, args.limit - processed)

            papers = connection.execute(
                SELECT_PENDING_SQL,
                (last_id, MODEL, batch_limit),
            ).fetchall()

            if not papers:
                break

            texts = prepare_texts(papers, encoding)
            vectors = embeddings.embed_documents(texts)

            save_batch(connection, papers, vectors)

            processed += len(papers)
            last_id = papers[-1][0]

            print(
                f"Saved {processed} embeddings this run; "
                f"last paper: {last_id}",
                flush=True,
            )

    print(json.dumps({
        "model": MODEL,
        "dimensions": DIMENSIONS,
        "embeddings_saved_this_run": processed,
        "elapsed_seconds": round(perf_counter() - started_at, 2),
    }, indent=2))


if __name__ == "__main__":
    main()