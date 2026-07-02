"""Append-only JSONL read/write — the seam that makes the whole pipeline "dump everything
to disk, reload for analysis," which is what makes raw-results-checked-in reproducibility
tractable."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


def write_jsonl(
    path: Path, items: list[Any], to_dict: Callable[[Any], dict] = lambda x: x.to_dict()
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for item in items:
            f.write(json.dumps(to_dict(item)) + "\n")


def append_jsonl(
    path: Path, item: Any, to_dict: Callable[[Any], dict] = lambda x: x.to_dict()
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(to_dict(item)) + "\n")


def read_jsonl(path: Path, from_dict: Callable[[dict], T]) -> list[T]:
    if not path.exists():
        return []
    items = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(from_dict(json.loads(line)))
    return items
