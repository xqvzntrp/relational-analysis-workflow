"""Human-readable execution reporting."""

from __future__ import annotations

from pathlib import Path

from execution_errors import ExecutionIssue


def format_execution_issue(issue: ExecutionIssue) -> str:
    subject = f"Step {issue.step} ({issue.mode})"
    return (
        f"{subject} stopped because {issue.message}\n"
        f"  What to do: {issue.hint}"
    )


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
        format_execution_issue(issue),
    ]

    if verbose:
        lines.append(f"  Execution type: {issue.problem_type}")

    lines.append("")
    lines.append("Later manifest steps were not executed.")
    return "\n".join(lines)
