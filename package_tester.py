"""Package-level validation, execution, contract, and artifact testing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from artifact_checker import ArtifactCheck, check_expected_artifacts
from artifact_spec import ArtifactSpecIssue, read_artifact_expectations
from authority_validator import validate_authority_progression
from dependency_validator import validate_dependencies
from executor import ExecutionOutcome, execute_manifest
from grain_spec import GrainIssue, read_grain_declarations
from manifest_validator import validate_manifest
from relation_contract import ContractIssue, read_relation_contract
from relation_contract_validator import (
    RuntimeContractIssue,
    runtime_contract_issues,
    validate_contract_declarations,
)


@dataclass(frozen=True)
class PackageTestResult:
    manifest: Path
    preflight_issues: tuple[Any, ...]
    execution: ExecutionOutcome | None
    runtime_contract_issues: tuple[RuntimeContractIssue, ...]
    artifact_spec_issues: tuple[ArtifactSpecIssue, ...]
    artifact_checks: tuple[ArtifactCheck, ...]

    @property
    def passed(self) -> bool:
        return (
            not self.preflight_issues
            and self.execution is not None
            and not self.execution.validation_issues
            and self.execution.execution_issue is None
            and not self.runtime_contract_issues
            and not self.artifact_spec_issues
            and all(check.matches for check in self.artifact_checks)
        )


def _preflight(manifest: Path) -> list[Any]:
    issues: list[Any] = list(validate_manifest(manifest))
    if issues:
        return issues

    dependency_issues = validate_dependencies(manifest)
    if dependency_issues:
        return list(dependency_issues)

    authority_issues = validate_authority_progression(manifest)
    if authority_issues:
        return list(authority_issues)

    _, grain_issues = read_grain_declarations(manifest)
    if grain_issues:
        return list(grain_issues)

    _, parse_contract_issues = read_relation_contract(manifest)
    if parse_contract_issues:
        return list(parse_contract_issues)

    contract_issues = validate_contract_declarations(manifest)
    if contract_issues:
        return list(contract_issues)

    _, artifact_spec_issues = read_artifact_expectations(manifest)
    if artifact_spec_issues:
        return list(artifact_spec_issues)

    return []


def _runtime_contract_checks(manifest: Path) -> list[RuntimeContractIssue]:
    """Open the completed package database and verify declared contracts."""
    declarations, parse_issues = read_relation_contract(manifest)
    if parse_issues or not declarations:
        return []

    # DuckDB remains an execution dependency; import it only for package tests.
    import duckdb

    database = manifest.resolve().parent / "artifacts" / "package.duckdb"
    connection = duckdb.connect(str(database), read_only=True)
    try:
        relations = sorted({item.relation for item in declarations})
        issues: list[RuntimeContractIssue] = []
        for relation in relations:
            issues.extend(
                runtime_contract_issues(connection, relation, declarations)
            )
        return issues
    finally:
        connection.close()


def test_package(manifest: Path) -> PackageTestResult:
    """Run the complete package test lifecycle."""
    manifest = manifest.resolve()
    preflight_issues = _preflight(manifest)
    if preflight_issues:
        return PackageTestResult(
            manifest=manifest,
            preflight_issues=tuple(preflight_issues),
            execution=None,
            runtime_contract_issues=(),
            artifact_spec_issues=(),
            artifact_checks=(),
        )

    execution = execute_manifest(manifest)
    if execution.validation_issues or execution.execution_issue is not None:
        return PackageTestResult(
            manifest=manifest,
            preflight_issues=(),
            execution=execution,
            runtime_contract_issues=(),
            artifact_spec_issues=(),
            artifact_checks=(),
        )

    runtime_issues = _runtime_contract_checks(manifest)
    expectations, artifact_spec_issues = read_artifact_expectations(manifest)
    checks = (
        []
        if artifact_spec_issues
        else check_expected_artifacts(manifest, expectations)
    )

    return PackageTestResult(
        manifest=manifest,
        preflight_issues=(),
        execution=execution,
        runtime_contract_issues=tuple(runtime_issues),
        artifact_spec_issues=tuple(artifact_spec_issues),
        artifact_checks=tuple(checks),
    )
