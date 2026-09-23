"""Human-readable reporting for manifest validation."""

from __future__ import annotations

from pathlib import Path

from manifest_validator import ValidationIssue


def format_issue(issue: ValidationIssue) -> str:
    """Render one validation issue as concise prose."""
    subject = f"Step {issue.step}" if issue.step != "-" else "Manifest"
    return (
        f"{subject} failed because {issue.message}\n"
        f"  What to do: {issue.hint}"
    )


def format_validation_report(
    manifest: Path,
    issues: list[ValidationIssue],
    *,
    verbose: bool = False,
) -> str:
    """Render a complete validation report for command-line use."""
    lines: list[str] = []

    lines.append(f"Dry run for {manifest}")

    if not issues:
        lines.append("Result: ready to run.")
        if verbose:
            lines.append("No manifest validation problems were found.")
        return "\n".join(lines)

    count = len(issues)
    noun = "problem" if count == 1 else "problems"
    lines.append(f"Result: not ready to run. Found {count} {noun}.")

    for index, issue in enumerate(issues, start=1):
        lines.append("")
        lines.append(f"{index}. {format_issue(issue)}")
        if verbose:
            lines.append(f"  Validation type: {issue.problem_type}")

    lines.append("")
    lines.append("No package steps were executed.")
    return "\n".join(lines)
