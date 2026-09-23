"""Best-effort SQL relation dependency discovery.

This module intentionally does not try to become a full SQL parser.
It extracts a conservative set of relations created and referenced by
the SQL patterns used by the analytical package.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


_CREATE_PATTERNS = (
    re.compile(
        r"\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:VIEW|TABLE)\s+"
        r'(?P<name>"[^"]+"|[A-Za-z_][A-Za-z0-9_]*)',
        re.IGNORECASE,
    ),
)

_REFERENCE_PATTERNS = (
    re.compile(
        r"\bFROM\s+(?P<name>\"[^\"]+\"|[A-Za-z_][A-Za-z0-9_]*)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bJOIN\s+(?P<name>\"[^\"]+\"|[A-Za-z_][A-Za-z0-9_]*)",
        re.IGNORECASE,
    ),
)


@dataclass(frozen=True)
class SqlDependencies:
    sql_path: Path
    creates: tuple[str, ...]
    references: tuple[str, ...]


def _normalize_identifier(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1].replace('""', '"')
    return value


def discover_sql_dependencies(sql_path: Path) -> SqlDependencies:
    """Discover relations created and referenced by a SQL file."""
    sql_path = sql_path.resolve()
    text = sql_path.read_text(encoding="utf-8")

    creates: list[str] = []
    references: list[str] = []

    for pattern in _CREATE_PATTERNS:
        for match in pattern.finditer(text):
            name = _normalize_identifier(match.group("name"))
            if name not in creates:
                creates.append(name)

    for pattern in _REFERENCE_PATTERNS:
        for match in pattern.finditer(text):
            name = _normalize_identifier(match.group("name"))
            if name not in references:
                references.append(name)

    # A relation created by the file is not considered an external dependency
    # merely because it is referenced later in the same file.
    external_references = [
        name for name in references if name not in set(creates)
    ]

    return SqlDependencies(
        sql_path=sql_path,
        creates=tuple(creates),
        references=tuple(external_references),
    )
