import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any
import hashlib
from datetime import date
import psycopg
from email.utils import parsedate_to_datetime

def iter_records(file_path: Path) -> Iterator[dict[str, Any]]:
    with file_path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                yield json.loads(line)

def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())

def compute_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def prepare_paper(record: dict[str, Any]) -> dict[str, Any]:
    paper = {
        "arxiv_id": record["id"],
        "title": normalize_whitespace(record["title"]),
        "abstract": normalize_whitespace(record["abstract"]),
        "authors": normalize_whitespace(record["authors"]),
        "categories": record["categories"].split(),
        "published_at": parsedate_to_datetime(
            record["versions"][0]["created"]
        ),
        "source_updated_on": date.fromisoformat(record["update_date"]),
    }
    
    hash_data = paper.copy()
    hash_data["published_at"] = paper["published_at"].isoformat()
    hash_data["source_updated_on"] = paper["source_updated_on"].isoformat()

    serialized = json.dumps(hash_data, sort_keys=True, ensure_ascii=False)
    paper["content_hash"] = compute_content_hash(serialized)

    return paper

def insert_paper(connection: psycopg.Connection, paper: dict[str, Any]) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO papers (
                arxiv_id, title, abstract, authors, categories,
                published_at, source_updated_on, content_hash
            )
            VALUES (
                %(arxiv_id)s, %(title)s, %(abstract)s, %(authors)s,
                %(categories)s, %(published_at)s,
                %(source_updated_on)s, %(content_hash)s
            )
            ON CONFLICT (arxiv_id) DO UPDATE SET
            title = EXCLUDED.title,
            abstract = EXCLUDED.abstract,
            authors = EXCLUDED.authors,
            categories = EXCLUDED.categories,
            published_at = EXCLUDED.published_at,
            source_updated_on = EXCLUDED.source_updated_on,
            content_hash = EXCLUDED.content_hash
            """,
            paper,
        )