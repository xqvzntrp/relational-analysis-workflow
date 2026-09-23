#!/usr/bin/env python3
"""Manifest-driven analytical package runner.

v018 adds optional relation contracts for columns, keys, and types.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from artifact_checker import check_expected_artifacts
from artifact_spec import read_artifact_expectations
from authority_validator import validate_authority_progression
from dependency_plan import discover_manifest_dependencies
from dependency_validator import validate_dependencies
from dry_run_json import build_dry_run_document
from execution_reporter import format_execution_failure
from executor import database_path_for_manifest, execute_manifest
from manifest_inspector import inspect_manifest
from manifest_schema import AUTHORITY_ZONES, MANIFEST_COLUMNS, MODES
from grain_analysis import analyze_grain
from manifest_validator import validate_manifest
from package_summary import summarize_package
from package_tester import test_package
from package_test_reporter import format_package_test_report
from relation_contract import read_relation_contract
from relation_contract_validator import validate_contract_declarations
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
    mode.add_argument("--test", action="store_true",
                      help="Run the complete package test lifecycle.")

    parser.add_argument("--verbose", action="store_true",
                        help="Show additional diagnostic information.")
    parser.add_argument("--json", action="store_true",
                        help="Emit dry-run results as machine-readable JSON.")
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
    grain_analysis = None
    relation_contracts = None
    contract_issues = []

    if not issues:
        dependencies = discover_manifest_dependencies(manifest)
        dependency_issues = validate_dependencies(manifest)
        if not dependency_issues:
            authority_issues = validate_authority_progression(manifest)

        relation_contracts, parse_contract_issues = read_relation_contract(manifest)
        contract_issues = (
            parse_contract_issues
            if parse_contract_issues
            else validate_contract_declarations(manifest)
        )

        if verbose:
            inspections = inspect_manifest(manifest)
            summary = summarize_package(manifest)
            grain_analysis = analyze_grain(manifest)

    print(format_validation_report(
        manifest,
        issues,
        verbose=verbose,
        inspections=inspections,
        dependencies=dependencies,
        dependency_issues=dependency_issues,
        authority_issues=authority_issues,
        package_summary=summary,
        grain_analysis=grain_analysis,
        relation_contracts=relation_contracts,
        contract_issues=contract_issues,
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

    expectations, artifact_spec_issues = read_artifact_expectations(manifest)
    if artifact_spec_issues:
        print()
        print("Artifact specification problems:")
        for issue in artifact_spec_issues:
            print(f"  {issue.problem_type}: {issue.message}")
            print(f"    What to do: {issue.hint}")
        return 1

    checks = check_expected_artifacts(manifest, expectations)

    print()
    print("Deterministic artifact checks:")
    if not checks:
        print("  (none declared)")
    else:
        for check in checks:
            status = "match" if check.matches else "DIFF"
            print(f"  {status}: {check.artifact} (expected {check.expected})")
            if check.matches and verbose and check.artifact_sha256:
                print(f"    sha256: {check.artifact_sha256}")
            if not check.matches:
                print(f"    {check.summary}")
                for detail in check.details:
                    print(f"    {detail}")

    print()
    if any(not check.matches for check in checks):
        print("Run completed, but deterministic artifact checks failed.")
        return 1

    print("Run completed.")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.json:
        if not args.dry_run:
            parser.error("--json is only valid with --dry-run")
        document = build_dry_run_document(args.manifest, verbose=args.verbose)
        print(json.dumps(document, indent=2, sort_keys=True))
        return 0 if document["ready"] else 1

    if args.dry_run:
        return print_validation_report(args.manifest, args.verbose)

    if args.test:
        result = test_package(args.manifest)
        print(format_package_test_report(result, verbose=args.verbose))
        return 0 if result.passed else 1

    return print_execution_report(args.manifest, args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
