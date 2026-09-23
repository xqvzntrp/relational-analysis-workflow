#!/usr/bin/env python3
"""Manifest-driven analytical package runner.

v016 adds a package summary to successful verbose dry run.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from authority_validator import validate_authority_progression
from dependency_plan import discover_manifest_dependencies
from dependency_validator import validate_dependencies
from execution_reporter import format_execution_failure
from executor import database_path_for_manifest, execute_manifest
from manifest_inspector import inspect_manifest
from manifest_schema import AUTHORITY_ZONES, MANIFEST_COLUMNS, MODES
from manifest_validator import validate_manifest
from package_summary import summarize_package
from validation_reporter import format_validation_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="Run or validate a manifest-driven analytical package.",
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true",
                      help="Validate the package without executing it.")
    mode.add_argument("--run", action="store_true",
                      help="Execute the package.")

    parser.add_argument("--verbose", action="store_true",
                        help="Show additional diagnostic information.")
    parser.add_argument("manifest", type=Path,
                        help="Path to the package manifest CSV.")
    return parser


def print_validation_report(manifest: Path, verbose: bool) -> int:
    issues = validate_manifest(manifest)
    dependency_issues = []
    authority_issues = []
    inspections = None
    dependencies = None
    summary = None

    if not issues:
        dependencies = discover_manifest_dependencies(manifest)
        dependency_issues = validate_dependencies(manifest)
        if not dependency_issues:
            authority_issues = validate_authority_progression(manifest)
        if verbose:
            inspections = inspect_manifest(manifest)
            summary = summarize_package(manifest)

    print(format_validation_report(
        manifest,
        issues,
        verbose=verbose,
        inspections=inspections,
        dependencies=dependencies,
        dependency_issues=dependency_issues,
        authority_issues=authority_issues,
        package_summary=summary,
    ))

    if not issues and not dependency_issues and not authority_issues and verbose:
        print()
        print("Manifest contract:")
        print(f"  Columns: {', '.join(MANIFEST_COLUMNS)}")
        print(f"  Modes: {', '.join(MODES)}")
        print(f"  Authority zones: {', '.join(AUTHORITY_ZONES)}")

    return 0 if not issues and not dependency_issues and not authority_issues else 1


def print_execution_report(manifest: Path, verbose: bool) -> int:
    outcome = execute_manifest(manifest)

    if outcome.validation_issues:
        print(format_validation_report(
            manifest,
            outcome.validation_issues,
            verbose=verbose,
        ))
        return 1

    if outcome.execution_issue is not None:
        print(format_execution_failure(
            manifest,
            completed_steps=len(outcome.results),
            issue=outcome.execution_issue,
            verbose=verbose,
        ))
        return 1

    print(f"Run for {manifest}")
    print(f"Database: {database_path_for_manifest(manifest)}")
    print(
        f"Execution plan: {len(outcome.results)} "
        f"{'step' if len(outcome.results) == 1 else 'steps'}."
    )

    for result in outcome.results:
        print()
        print(f"Step {result.step}: {result.mode}")
        print(f"  Status: {result.status}")
        print(f"  {result.message}")

    print()
    print("Run completed.")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.dry_run:
        return print_validation_report(args.manifest, args.verbose)

    return print_execution_report(args.manifest, args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
