"""Execution engine for manifest-driven packages.

v008 implements load_csv and run_sql.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb

from manifest_inspector import inspect_manifest
from manifest_validator import validate_manifest
from mode_handlers import load_csv, run_sql


@dataclass(frozen=True)
class ExecutionResult:
    step: str
    mode: str
    status: str
    message: str


def database_path_for_manifest(path: Path) -> Path:
    """Return the package-local execution database path."""
    artifacts_dir = path.resolve().parent / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    return artifacts_dir / "package.duckdb"


def execute_manifest(path: Path) -> tuple[list[ExecutionResult], list]:
    """Validate, then execute supported manifest steps in order."""
    issues = validate_manifest(path)
    if issues:
        return [], issues

    rows = inspect_manifest(path)
    results: list[ExecutionResult] = []
    database_path = database_path_for_manifest(path)

    # Fresh-run discipline: recreate the execution database each run.
    if database_path.exists():
        database_path.unlink()

    connection = duckdb.connect(str(database_path))

    try:
        for row in rows:
            if row.mode == "load_csv":
                row_count = load_csv(
                    connection,
                    Path(row.resolved_input or ""),
                    row.output_value,
                )
                results.append(
                    ExecutionResult(
                        step=row.step,
                        mode=row.mode,
                        status="completed",
                        message=(
                            f"Loaded {row_count} rows from "
                            f"{row.input_value!r} into relation "
                            f"{row.output_value!r}."
                        ),
                    )
                )
                continue

            if row.mode == "run_sql":
                run_sql(
                    connection,
                    Path(row.resolved_input or ""),
                )
                results.append(
                    ExecutionResult(
                        step=row.step,
                        mode=row.mode,
                        status="completed",
                        message=f"Executed SQL file {row.input_value!r}.",
                    )
                )
                continue

            results.append(
                ExecutionResult(
                    step=row.step,
                    mode=row.mode,
                    status="pending",
                    message=f"Execution handler for {row.mode!r} is not implemented yet.",
                )
            )
    finally:
        connection.close()

    return results, []
