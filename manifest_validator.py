"""Manifest validation for dry-run mode."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from manifest_schema import AUTHORITY_ZONES, MANIFEST_COLUMNS, MODES


@dataclass(frozen=True)
class ValidationIssue:
    step: str
    problem_type: str
    message: str
    hint: str


def validate_manifest(path: Path) -> list[ValidationIssue]:
    """Validate manifest structure and row values without executing work."""
    issues: list[ValidationIssue] = []

    if not path.exists():
        return [
            ValidationIssue(
                step="-",
                problem_type="manifest_missing",
                message=f"Manifest does not exist: {path}",
                hint="Check the path and try again.",
            )
        ]

    if not path.is_file():
        return [
            ValidationIssue(
                step="-",
                problem_type="manifest_not_file",
                message=f"Manifest path is not a file: {path}",
                hint="Pass the path to a CSV manifest file.",
            )
        ]

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)

            actual_columns = tuple(reader.fieldnames or ())
            if actual_columns != MANIFEST_COLUMNS:
                issues.append(
                    ValidationIssue(
                        step="-",
                        problem_type="invalid_header",
                        message=(
                            "Manifest header does not match the required schema. "
                            f"Found: {', '.join(actual_columns) or '(none)'}"
                        ),
                        hint=f"Use exactly: {', '.join(MANIFEST_COLUMNS)}",
                    )
                )
                return issues

            seen_steps: set[int] = set()

            for line_number, row in enumerate(reader, start=2):
                raw_step = (row["step"] or "").strip()
                mode = (row["mode"] or "").strip()
                input_value = (row["input"] or "").strip()
                output_value = (row["output"] or "").strip()
                authority_zone = (row["authority_zone"] or "").strip()

                step_label = raw_step or f"line {line_number}"

                try:
                    step_number = int(raw_step)
                    if step_number < 1:
                        raise ValueError
                except ValueError:
                    issues.append(
                        ValidationIssue(
                            step=step_label,
                            problem_type="invalid_step",
                            message=f"Step must be a positive integer; found {raw_step!r}.",
                            hint="Use values such as 1, 2, 3.",
                        )
                    )
                else:
                    if step_number in seen_steps:
                        issues.append(
                            ValidationIssue(
                                step=step_label,
                                problem_type="duplicate_step",
                                message=f"Step {step_number} appears more than once.",
                                hint="Give every manifest row a unique step number.",
                            )
                        )
                    seen_steps.add(step_number)

                if mode not in MODES:
                    issues.append(
                        ValidationIssue(
                            step=step_label,
                            problem_type="invalid_mode",
                            message=f"Mode {mode!r} is not allowed.",
                            hint=f"Use one of: {', '.join(MODES)}",
                        )
                    )

                if authority_zone not in AUTHORITY_ZONES:
                    issues.append(
                        ValidationIssue(
                            step=step_label,
                            problem_type="invalid_authority_zone",
                            message=f"Authority zone {authority_zone!r} is not allowed.",
                            hint=f"Use one of: {', '.join(AUTHORITY_ZONES)}",
                        )
                    )

                if not input_value:
                    issues.append(
                        ValidationIssue(
                            step=step_label,
                            problem_type="missing_input",
                            message="Input is required.",
                            hint="Provide a source path, SQL path, or relation/query input.",
                        )
                    )

                if mode in {"load_csv", "export_sql"} and not output_value:
                    issues.append(
                        ValidationIssue(
                            step=step_label,
                            problem_type="missing_output",
                            message=f"Output is required for mode {mode!r}.",
                            hint="Provide the target relation or export path.",
                        )
                    )

    except (OSError, UnicodeError, csv.Error) as exc:
        issues.append(
            ValidationIssue(
                step="-",
                problem_type="manifest_unreadable",
                message=f"Manifest could not be read: {exc}",
                hint="Confirm the file is a readable UTF-8 CSV.",
            )
        )

    return issues
