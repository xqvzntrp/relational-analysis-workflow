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
