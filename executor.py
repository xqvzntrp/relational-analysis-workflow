"""Execution engine for manifest-driven packages.

v010 adds structured execution error handling and prose diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb

from authority_validator import validate_authority_progression
from dependency_validator import validate_dependencies
from execution_errors import ExecutionIssue
from manifest_inspector import inspect_manifest
from manifest_validator import validate_manifest
from mode_handlers import export_sql, load_csv, run_sql
from sql_diagnostics import build_sql_failure_context


@dataclass(frozen=True)
class ExecutionResult:
    step: str
    mode: str
    status: str
    message: str


@dataclass(frozen=True)
class ExecutionOutcome:
    results: list[ExecutionResult]
    validation_issues: list
    execution_issue: ExecutionIssue | None


def database_path_for_manifest(path: Path) -> Path:
    """Return the package-local execution database path."""
    artifacts_dir = path.resolve().parent / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    return artifacts_dir / "package.duckdb"


def _execution_issue_for_exception(row, exc: Exception) -> ExecutionIssue:
    if isinstance(exc, FileNotFoundError):
        problem_type = "input_missing"
        hint = "Check the manifest path and confirm the referenced input file exists."
    elif isinstance(exc, PermissionError):
        problem_type = "permission_denied"
        hint = "Check read/write permissions for the referenced file or output directory."
    elif isinstance(exc, UnicodeError):
        problem_type = "text_encoding_error"
        hint = "Save text inputs as UTF-8 and try again."
    elif isinstance(exc, duckdb.Error):
        problem_type = "duckdb_error"
        hint = (
            "Check the SQL location shown below, then verify relation names, "
            "column names, and dependencies created by earlier manifest steps."
        )
    elif isinstance(exc, ValueError):
        problem_type = "invalid_execution_input"
        hint = "Check the values declared by this manifest step."
    else:
        problem_type = "execution_error"
        hint = "Review this step's input and try the run again."

    input_path = row.resolved_input
    sql_line_number = None
    sql_line_text = None
    creates: tuple[str, ...] = ()
    references: tuple[str, ...] = ()

    if row.mode == "run_sql" and input_path:
        sql_path = Path(input_path)
        if sql_path.exists():
            context = build_sql_failure_context(
                sql_path,
                str(exc) or exc.__class__.__name__,
            )
            input_path = str(context.sql_path)
            sql_line_number = context.line_number
            sql_line_text = context.line_text
            creates = context.creates
            references = context.references

    return ExecutionIssue(
        step=row.step,
        mode=row.mode,
        problem_type=problem_type,
        message=str(exc) or exc.__class__.__name__,
        hint=hint,
        input_path=input_path,
        sql_line_number=sql_line_number,
        sql_line_text=sql_line_text,
        creates=creates,
        references=references,
    )


def execute_manifest(path: Path) -> ExecutionOutcome:
    """Validate, then execute manifest steps in order until completion or failure."""
    validation_issues = validate_manifest(path)
    if validation_issues:
        return ExecutionOutcome(
            results=[],
            validation_issues=validation_issues,
            execution_issue=None,
        )

    dependency_issues = validate_dependencies(path)
    if dependency_issues:
        # Reuse the validation channel so execution never starts.
        return ExecutionOutcome(
            results=[],
            validation_issues=dependency_issues,
            execution_issue=None,
        )

    authority_issues = validate_authority_progression(path)
    if authority_issues:
        return ExecutionOutcome(
            results=[],
            validation_issues=authority_issues,
            execution_issue=None,
        )

    rows = inspect_manifest(path)
    results: list[ExecutionResult] = []
    database_path = database_path_for_manifest(path)

    if database_path.exists():
        database_path.unlink()

    connection = duckdb.connect(str(database_path))

    try:
        for row in rows:
            try:
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

                if row.mode == "export_sql":
                    row_count = export_sql(
                        connection,
                        row.input_value,
                        Path(row.resolved_output or ""),
                    )
                    results.append(
                        ExecutionResult(
                            step=row.step,
                            mode=row.mode,
                            status="completed",
                            message=(
                                f"Exported {row_count} rows from "
                                f"{row.input_value!r} to {row.output_value!r}."
                            ),
                        )
                    )
                    continue

                raise ValueError(f"Unsupported manifest mode: {row.mode}")

            except Exception as exc:
                return ExecutionOutcome(
                    results=results,
                    validation_issues=[],
                    execution_issue=_execution_issue_for_exception(row, exc),
                )
    finally:
        connection.close()

    return ExecutionOutcome(
        results=results,
        validation_issues=[],
        execution_issue=None,
    )
