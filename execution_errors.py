"""Structured execution errors and prose diagnostics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionIssue:
    step: str
    mode: str
    problem_type: str
    message: str
    hint: str
    input_path: str | None = None
    sql_line_number: int | None = None
    sql_line_text: str | None = None
    creates: tuple[str, ...] = ()
    references: tuple[str, ...] = ()
