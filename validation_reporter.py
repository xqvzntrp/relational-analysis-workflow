"""Human-readable reporting for manifest validation."""

from __future__ import annotations

from pathlib import Path

from manifest_inspector import ManifestRowInspection
from manifest_validator import ValidationIssue
from dependency_plan import StepDependency
from dependency_validator import DependencyIssue


def format_issue(issue: ValidationIssue) -> str:
    """Render one validation issue as concise prose."""
    subject = f"Step {issue.step}" if issue.step != "-" else "Manifest"
    return (
        f"{subject} failed because {issue.message}\n"
        f"  What to do: {issue.hint}"
    )


def format_dependency_issue(issue: DependencyIssue) -> str:
    """Render one dependency issue as concise prose."""
    return (
        f"Step {issue.step} [{issue.authority_zone}] failed because "
        f"{issue.message}\n"
        f"  What to do: {issue.hint}"
    )


def format_row_inspection(row: ManifestRowInspection) -> str:
    """Render one manifest row for verbose dry-run output."""
    lines = [
        f"Step {row.step} on line {row.line_number}:",
        f"  Mode: {row.mode}",
        f"  Authority zone: {row.authority_zone}",
        f"  Input: {row.input_value or '(none)'}",
        f"  Output: {row.output_value or '(none)'}",
    ]
    if row.resolved_input:
        lines.append(f"  Resolved input: {row.resolved_input}")
    if row.resolved_output:
        lines.append(f"  Resolved output: {row.resolved_output}")
    return "\n".join(lines)


def format_validation_report(
    manifest: Path,
    issues: list[ValidationIssue],
    *,
    verbose: bool = False,
    inspections: list[ManifestRowInspection] | None = None,
    dependencies: list[StepDependency] | None = None,
    dependency_issues: list[DependencyIssue] | None = None,
) -> str:
    """Render a complete validation report for command-line use."""
    lines: list[str] = [f"Dry run for {manifest}"]

    dependency_issues = dependency_issues or []

    if not issues and not dependency_issues:
        lines.append("Result: ready to run.")
        if verbose:
            lines.append("No manifest or dependency validation problems were found.")
            if inspections is not None:
                count = len(inspections)
                lines.append("")
                lines.append(f"Execution plan: {count} {'step' if count == 1 else 'steps'}.")
                for row in inspections:
                    lines.append("")
                    lines.append(format_row_inspection(row))

            if dependencies is not None:
                lines.append("")
                lines.append("Discovered relation dependencies:")
                for dep in dependencies:
                    created = ", ".join(dep.creates) if dep.creates else "(none)"
                    referenced = ", ".join(dep.references) if dep.references else "(none)"
                    lines.append(
                        f"  Step {dep.step} [{dep.authority_zone}] "
                        f"creates: {created}; references: {referenced}"
                    )
        return "\n".join(lines)

    if not issues and dependency_issues:
        count = len(dependency_issues)
        lines.append(
            f"Result: not ready to run. Found {count} "
            f"{'dependency problem' if count == 1 else 'dependency problems'}."
        )

        for index, issue in enumerate(dependency_issues, start=1):
            lines.append("")
            lines.append(f"{index}. {format_dependency_issue(issue)}")
            if verbose:
                lines.append(f"  Validation type: {issue.problem_type}")

        if verbose and dependencies is not None:
            lines.append("")
            lines.append("Discovered relation dependencies:")
            for dep in dependencies:
                created = ", ".join(dep.creates) if dep.creates else "(none)"
                referenced = ", ".join(dep.references) if dep.references else "(none)"
                lines.append(
                    f"  Step {dep.step} [{dep.authority_zone}] "
                    f"creates: {created}; references: {referenced}"
                )

        lines.append("")
        lines.append("No package steps were executed.")
        return "\n".join(lines)

    count = len(issues)
    lines.append(
        f"Result: not ready to run. Found {count} "
        f"{'problem' if count == 1 else 'problems'}."
    )

    for index, issue in enumerate(issues, start=1):
        lines.append("")
        lines.append(f"{index}. {format_issue(issue)}")
        if verbose:
            lines.append(f"  Validation type: {issue.problem_type}")

    lines.append("")
    lines.append("No package steps were executed.")
    return "\n".join(lines)
