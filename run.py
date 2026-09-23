#!/usr/bin/env python3
"""Manifest-driven analytical package runner.

Commit 1 establishes the command-line contract only.
Execution and validation logic will be added in later commits.
"""

from __future__ import annotations

import argparse
from pathlib import Path


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


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    mode_name = "dry-run" if args.dry_run else "run"

    print(f"Mode: {mode_name}")
    print(f"Manifest: {args.manifest}")

    if args.verbose:
        print("Verbose: enabled")

    print("Status: command recognized; implementation pending.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
