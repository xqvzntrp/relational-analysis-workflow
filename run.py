#!/usr/bin/env python3
"""Manifest-driven analytical package runner.

v009 implements all three execution modes with DuckDB.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from executor import database_path_for_manifest, execute_manifest
from manifest_inspector import inspect_manifest
from manifest_schema import AUTHORITY_ZONES, MANIFEST_COLUMNS, MODES
from manifest_validator import validate_manifest
from validation_reporter import format_validation_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="Run or validate a manifest-driven analytical package.",
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the package without executing it.",
    )
    mode.add_argument(
        "--run",
        action="store_true",
        help="Execute the package.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show additional diagnostic information.",
    )
    parser.add_argument(
        "manifest",
        type=Path,
        help="Path to the package manifest CSV.",
    )
    return parser


def print_validation_report(manifest: Path, verbose: bool) -> int:
    issues = validate_manifest(manifest)
    inspections = inspect_manifest(manifest) if verbose and not issues else None

    print(
        format_validation_report(
            manifest,
            issues,
            verbose=verbose,
            inspections=inspections,
        )
    )

    if not issues and verbose:
        print()
        print("Manifest contract:")
        print(f"  Columns: {', '.join(MANIFEST_COLUMNS)}")
        print(f"  Modes: {', '.join(MODES)}")
        print(f"  Authority zones: {', '.join(AUTHORITY_ZONES)}")

    return 0 if not issues else 1


def print_execution_report(manifest: Path, verbose: bool) -> int:
    results, issues = execute_manifest(manifest)

    if issues:
        print(format_validation_report(manifest, issues, verbose=verbose))
        return 1

    print(f"Run for {manifest}")
    print(f"Database: {database_path_for_manifest(manifest)}")
    print(f"Execution plan: {len(results)} {'step' if len(results) == 1 else 'steps'}.")

    for result in results:
        print()
        print(f"Step {result.step}: {result.mode}")
        print(f"  Status: {result.status}")
        print(f"  {result.message}")

    pending = [result for result in results if result.status == "pending"]

    print()
    if pending:
        print(
            f"Run finished with {len(pending)} "
            f"{'pending step' if len(pending) == 1 else 'pending steps'}."
        )
    else:
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
