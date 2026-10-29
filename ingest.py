import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

def iter_records(file_path: Path) -> Iterator[dict[str, Any]]:
    with file_path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                yield json.loads(line)

def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())