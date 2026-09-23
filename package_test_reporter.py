"""Human-readable package test reporting."""

from __future__ import annotations

from package_tester import PackageTestResult


def format_package_test_report(
    result: PackageTestResult,
    *,
    verbose: bool = False,
) -> str:
    lines = [
        f"Package test for {result.manifest}",
        "",
    ]

    if result.preflight_issues:
        lines.append("Preflight: FAIL")
        for issue in result.preflight_issues:
            lines.append(
                f"  {issue.problem_type}: {issue.message}"
            )
            lines.append(f"    What to do: {issue.hint}")
        lines.append("")
        lines.append("Execution was not started.")
        return "\n".join(lines)

    lines.append("Preflight: PASS")

    if result.execution is None:
        lines.append("Execution: NOT RUN")
        return "\n".join(lines)

    if result.execution.validation_issues:
        lines.append("Execution: FAIL")
        for issue in result.execution.validation_issues:
            lines.append(f"  {issue.problem_type}: {issue.message}")
        return "\n".join(lines)

    if result.execution.execution_issue is not None:
        issue = result.execution.execution_issue
        lines.append("Execution: FAIL")
        lines.append(
            f"  Step {issue.step} ({issue.mode}): {issue.message}"
        )
        if issue.input_path:
            lines.append(f"  Input: {issue.input_path}")
        if issue.sql_line_number is not None:
            lines.append(f"  SQL line: {issue.sql_line_number}")
        return "\n".join(lines)

    lines.append(
        f"Execution: PASS ({len(result.execution.results)} "
        f"{'step' if len(result.execution.results) == 1 else 'steps'})"
    )

    if result.runtime_contract_issues:
        lines.append("Relation contracts: FAIL")
        for issue in result.runtime_contract_issues:
            lines.append(f"  {issue.problem_type}: {issue.message}")
    else:
        lines.append("Relation contracts: PASS")

    if result.artifact_spec_issues:
        lines.append("Artifacts: FAIL")
        for issue in result.artifact_spec_issues:
            lines.append(f"  {issue.problem_type}: {issue.message}")
    elif not result.artifact_checks:
        lines.append("Artifacts: PASS (none declared)")
    else:
        failed = [item for item in result.artifact_checks if not item.matches]
        if failed:
            lines.append("Artifacts: FAIL")
            for check in failed:
                lines.append(
                    f"  DIFF: {check.artifact} "
                    f"(expected {check.expected})"
                )
                lines.append(f"    {check.summary}")
                for detail in check.details:
                    lines.append(f"    {detail}")
        else:
            lines.append(
                f"Artifacts: PASS ({len(result.artifact_checks)} checked)"
            )
            if verbose:
                for check in result.artifact_checks:
                    lines.append(
                        f"  match: {check.artifact} "
                        f"sha256={check.artifact_sha256}"
                    )

    lines.append("")
    lines.append("PACKAGE TEST: PASS" if result.passed else "PACKAGE TEST: FAIL")
    return "\n".join(lines)
