"""Execution skeleton for manifest-driven packages.

v006 establishes execution flow without implementing concrete modes yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from manifest_inspector import ManifestRowInspection, inspect_manifest
from manifest_validator import validate_manifest


@dataclass(frozen=True)
class ExecutionResult:
    step: str
    mode: str
    status: str
    message: str


def execute_manifest(path: Path) -> tuple[list[ExecutionResult], list]:
    """Validate first, then walk the manifest in order.

    Concrete handlers for load_csv, run_sql, and export_sql are intentionally
    deferred to later commits.
    """
    issues = validate_manifest(path)
    if issues:
        return [], issues

    rows = inspect_manifest(path)
    results: list[ExecutionResult] = []

    for row in rows:
        results.append(
            ExecutionResult(
                step=row.step,
                mode=row.mode,
                status="pending",
                message=f"Execution handler for {row.mode!r} is not implemented yet.",
            )
        )

    return results, []
