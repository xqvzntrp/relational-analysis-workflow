"""Human-readable execution reporting."""

from __future__ import annotations

from pathlib import Path

from execution_errors import ExecutionIssue


def format_execution_issue(issue: ExecutionIssue, *, verbose: bool = False) -> str:
    subject = f"Step {issue.step} ({issue.mode})"
    lines = [
        f"{subject} stopped because {issue.message}",
        f"  What to do: {issue.hint}",
    ]

    if issue.input_path:
        lines.append(f"  Input: {issue.input_path}")

    if issue.sql_line_number is not None:
        lines.append(f"  SQL line: {issue.sql_line_number}")
        if issue.sql_line_text:
            lines.append(f"  SQL text: {issue.sql_line_text}")

    if verbose and issue.creates:
        lines.append(f"  SQL creates: {', '.join(issue.creates)}")

    if verbose and issue.references:
        lines.append(f"  SQL references: {', '.join(issue.references)}")

    return "\n".join(lines)


def format_execution_failure(
    manifest: Path,
    completed_steps: int,
    issue: ExecutionIssue,
    *,
    verbose: bool = False,
) -> str:
    lines = [
        f"Run for {manifest}",
        "Result: stopped before completion.",
        f"Completed steps before failure: {completed_steps}.",
        "",
        format_execution_issue(issue, verbose=verbose),
    ]

    if verbose:
        lines.append(f"  Execution type: {issue.problem_type}")

    lines.append("")
    lines.append("Later manifest steps were not executed.")
    return "\n".join(lines)
