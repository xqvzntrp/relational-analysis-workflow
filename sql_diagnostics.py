"""Build contextual diagnostics for SQL execution failures."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from dependency_discovery import discover_sql_dependencies


_LINE_PATTERNS = (
    re.compile(r"\bLINE\s+(?P<line>\d+)\b", re.IGNORECASE),
    re.compile(r"\bline\s+(?P<line>\d+)\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class SqlFailureContext:
    sql_path: Path
    line_number: int | None
    line_text: str | None
    creates: tuple[str, ...]
    references: tuple[str, ...]


def extract_line_number(message: str) -> int | None:
    for pattern in _LINE_PATTERNS:
        match = pattern.search(message)
        if match:
            return int(match.group("line"))
    return None


def build_sql_failure_context(
    sql_path: Path,
    exception_message: str,
) -> SqlFailureContext:
    """Collect file, line, and dependency context for a failed SQL step."""
    sql_path = sql_path.resolve()
    line_number = extract_line_number(exception_message)
    line_text = None

    if line_number is not None and sql_path.exists():
        lines = sql_path.read_text(encoding="utf-8").splitlines()
        if 1 <= line_number <= len(lines):
            line_text = lines[line_number - 1].strip()

    deps = discover_sql_dependencies(sql_path)

    return SqlFailureContext(
        sql_path=sql_path,
        line_number=line_number,
        line_text=line_text,
        creates=deps.creates,
        references=deps.references,
    )
