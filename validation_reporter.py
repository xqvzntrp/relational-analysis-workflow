"""Human-readable reporting for manifest validation."""

from __future__ import annotations

from pathlib import Path

from manifest_inspector import ManifestRowInspection
from manifest_validator import ValidationIssue
from dependency_plan import StepDependency
from dependency_validator import DependencyIssue
from authority_validator import AuthorityIssue
from package_summary import PackageSummary
from grain_analysis import GrainAnalysis
from relation_contract import ContractColumn, ContractIssue


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


def format_authority_issue(issue: AuthorityIssue) -> str:
    """Render one authority-zone issue as concise prose."""
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
    authority_issues: list[AuthorityIssue] | None = None,
    package_summary: PackageSummary | None = None,
    grain_analysis: GrainAnalysis | None = None,
    relation_contracts: list[ContractColumn] | None = None,
    contract_issues: list[ContractIssue] | None = None,
) -> str:
    """Render a complete validation report for command-line use."""
    lines: list[str] = [f"Dry run for {manifest}"]

    dependency_issues = dependency_issues or []
    authority_issues = authority_issues or []

    if not issues and not dependency_issues and not authority_issues:
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

            if package_summary is not None:
                lines.append("")
                lines.append("Package summary:")
                lines.append(f"  Steps: {package_summary.step_count}")

                mode_text = ", ".join(
                    f"{name}={count}"
                    for name, count in sorted(package_summary.mode_counts.items())
                ) or "(none)"
                lines.append(f"  Modes: {mode_text}")

                zone_text = ", ".join(
                    f"{name}={count}"
                    for name, count in sorted(package_summary.authority_zone_counts.items())
                ) or "(none)"
                lines.append(f"  Authority zones: {zone_text}")

                created = ", ".join(package_summary.created_relations) or "(none)"
                final_created = ", ".join(package_summary.final_created_relations) or "(none)"
                exports = ", ".join(package_summary.export_outputs) or "(none)"

                lines.append(f"  Relations created: {created}")
                lines.append(f"  Final created relations: {final_created}")
                lines.append(f"  Export outputs: {exports}")

            if relation_contracts is not None:
                lines.append("")
                lines.append("Declared relation contracts:")
                if not relation_contracts:
                    lines.append("  (none)")
                else:
                    current_relation = None
                    for item in relation_contracts:
                        if item.relation != current_relation:
                            current_relation = item.relation
                            lines.append(f"  {current_relation}:")
                        key_text = " key" if item.key else ""
                        lines.append(
                            f"    {item.column}: {item.data_type}{key_text}"
                        )

                if contract_issues:
                    lines.append("")
                    lines.append("Relation contract problems:")
                    for issue in contract_issues:
                        lines.append(
                            f"  {issue.problem_type}: {issue.message} "
                            f"What to do: {issue.hint}"
                        )

            if grain_analysis is not None:
                lines.append("")
                lines.append("Declared analytical grain:")
                if not grain_analysis.declarations:
                    lines.append("  (none)")
                else:
                    for declaration in grain_analysis.declarations:
                        lines.append(
                            f"  {declaration.relation}: "
                            f"{', '.join(declaration.keys)}"
                        )

                if grain_analysis.transitions:
                    lines.append("")
                    lines.append("Observed grain transitions:")
                    for transition in grain_analysis.transitions:
                        status = "changed" if transition.changed else "preserved"
                        lines.append(
                            f"  Step {transition.step} [{transition.authority_zone}] "
                            f"{transition.upstream_relation} "
                            f"({', '.join(transition.upstream_grain)}) -> "
                            f"{transition.relation} "
                            f"({', '.join(transition.grain)}): {status}"
                        )

                if grain_analysis.issues:
                    lines.append("")
                    lines.append("Grain specification warnings:")
                    for issue in grain_analysis.issues:
                        lines.append(
                            f"  {issue.problem_type}: {issue.message} "
                            f"What to do: {issue.hint}"
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

        if verbose and package_summary is not None:
            lines.append("")
            lines.append("Package summary:")
            lines.append(f"  Steps: {package_summary.step_count}")
            exports = ", ".join(package_summary.export_outputs) or "(none)"
            finals = ", ".join(package_summary.final_created_relations) or "(none)"
            lines.append(f"  Final created relations: {finals}")
            lines.append(f"  Export outputs: {exports}")

        if verbose and package_summary is not None:
            lines.append("")
            lines.append("Package summary:")
            lines.append(f"  Steps: {package_summary.step_count}")
            exports = ", ".join(package_summary.export_outputs) or "(none)"
            finals = ", ".join(package_summary.final_created_relations) or "(none)"
            lines.append(f"  Final created relations: {finals}")
            lines.append(f"  Export outputs: {exports}")

        lines.append("")
        lines.append("No package steps were executed.")
        return "\n".join(lines)

    if not issues and not dependency_issues and authority_issues:
        count = len(authority_issues)
        lines.append(
            f"Result: not ready to run. Found {count} "
            f"{'authority-zone problem' if count == 1 else 'authority-zone problems'}."
        )

        for index, issue in enumerate(authority_issues, start=1):
            lines.append("")
            lines.append(f"{index}. {format_authority_issue(issue)}")
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
