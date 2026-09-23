#!/usr/bin/env python3
"""Manifest-driven analytical package runner.

v005 adds verbose dry-run reporting.
Execution logic will be added in later commits.
"""

from __future__ import annotations

import argparse
from pathlib import Path

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
    inspections = inspect_manifest(manifest) if verbose and not issues else None

    print(format_validation_report(
        manifest,
        issues,
        verbose=verbose,
        inspections=inspections,
    ))

    if not issues and verbose:
        print()
        print("Manifest contract:")
        print(f"  Columns: {', '.join(MANIFEST_COLUMNS)}")
        print(f"  Modes: {', '.join(MODES)}")
        print(f"  Authority zones: {', '.join(AUTHORITY_ZONES)}")

    return 0 if not issues else 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.dry_run:
        return print_validation_report(args.manifest, args.verbose)

    print(f"Run: {args.manifest}")
    if args.verbose:
        print("Verbose: enabled")
    print("Status: execution not implemented yet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
