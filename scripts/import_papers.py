import json
import sys
from datetime import date

from app.database import get_connection


BATCH_SIZE = 50

UPSERT_SQL = """
INSERT INTO papers (
    arxiv_id,
    title,
    abstract,
    authors,
    categories,
    source_updated_on
)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (arxiv_id) DO UPDATE SET
    title = EXCLUDED.title,
    abstract = EXCLUDED.abstract,
    authors = EXCLUDED.authors,
    categories = EXCLUDED.categories,
    source_updated_on = EXCLUDED.source_updated_on
WHERE EXCLUDED.source_updated_on >= papers.source_updated_on;
"""


def parse_record(line):
    record = json.loads(line)

    required_fields = (
        "id",
        "title",
        "abstract",
        "authors",
        "categories",
        "update_date",
    )

    for field in required_fields:
        value = record.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a nonempty string")

    return (
        record["id"].strip(),
        " ".join(record["title"].split()),
        record["abstract"].strip(),
        record["authors"].strip(),
        record["categories"].split(),
        date.fromisoformat(record["update_date"]),
    )


def write_batch(connection, batch):
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.executemany(UPSERT_SQL, batch)


def main():
    batch = []
    processed = 0

    with get_connection() as connection:
        for line_number, line in enumerate(sys.stdin, start=1):
            if not line.strip():
                continue

            try:
                batch.append(parse_record(line))
            except (ValueError, KeyError, TypeError) as error:
                raise ValueError(
                    f"Invalid record on line {line_number}: {error}"
                ) from error

            if len(batch) >= BATCH_SIZE:
                write_batch(connection, batch)
                processed += len(batch)
                print(f"Processed {processed} records", flush=True)
                batch.clear()

        if batch:
            write_batch(connection, batch)
            processed += len(batch)

    print(f"Finished: processed {processed} records")


if __name__ == "__main__":
    main()