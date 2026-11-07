import json

import tiktoken

from app.database import get_connection


MODEL = "text-embedding-3-small"
PRICE_PER_MILLION_TOKENS = 0.02

# Conservative application limit below the documented 8,192-token maximum.
INPUT_TOKEN_LIMIT = 8000
READ_BATCH_SIZE = 200


def main():
    encoding = tiktoken.encoding_for_model(MODEL)

    paper_count = 0
    total_tokens = 0
    longest_input = 0
    oversized_ids = []
    last_id = ""

    with get_connection() as connection:
        while True:
            papers = connection.execute(
                """
                SELECT arxiv_id, title, abstract
                FROM papers
                WHERE arxiv_id > %s
                ORDER BY arxiv_id
                LIMIT %s;
                """,
                (last_id, READ_BATCH_SIZE),
            ).fetchall()

            if not papers:
                break

            for arxiv_id, title, abstract in papers:
                text = f"{title.strip()}\n\n{abstract.strip()}"

                token_count = len(
                    encoding.encode(text, disallowed_special=())
                )

                paper_count += 1
                total_tokens += token_count
                longest_input = max(longest_input, token_count)

                if token_count > INPUT_TOKEN_LIMIT:
                    oversized_ids.append(arxiv_id)

            last_id = papers[-1][0]

    report = {
        "model": MODEL,
        "papers": paper_count,
        "total_input_tokens": total_tokens,
        "longest_input_tokens": longest_input,
        "application_input_limit": INPUT_TOKEN_LIMIT,
        "oversized_paper_ids": oversized_ids,
        "estimated_embedding_cost_usd": round(
            total_tokens / 1_000_000 * PRICE_PER_MILLION_TOKENS,
            6,
        ),
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()