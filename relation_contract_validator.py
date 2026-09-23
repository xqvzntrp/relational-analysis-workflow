"""Static and runtime validation for optional relation contracts."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dependency_plan import discover_manifest_dependencies
from grain_spec import read_grain_declarations
from relation_contract import ContractColumn, ContractIssue, read_relation_contract


@dataclass(frozen=True)
class RuntimeContractIssue:
    relation: str
    column: str
    problem_type: str
    message: str
    hint: str


_TYPE_EQUIVALENTS = {
    "TEXT": "VARCHAR",
    "STRING": "VARCHAR",
    "INT": "INTEGER",
    "INT4": "INTEGER",
    "INT8": "BIGINT",
    "BOOL": "BOOLEAN",
}


def normalize_type(value: str) -> str:
    value = value.strip().upper()
    return _TYPE_EQUIVALENTS.get(value, value)


def validate_contract_declarations(manifest: Path) -> list[ContractIssue]:
    """Validate relation-contract declarations against package metadata."""
    declarations, issues = read_relation_contract(manifest)
    if issues:
        return issues

    created_relations = {
        relation
        for step in discover_manifest_dependencies(manifest)
        for relation in step.creates
    }

    grain_declarations, _ = read_grain_declarations(manifest)
    grain_by_relation = {
        declaration.relation: declaration.keys
        for declaration in grain_declarations
    }

    by_relation: dict[str, list[ContractColumn]] = defaultdict(list)
    for declaration in declarations:
        by_relation[declaration.relation].append(declaration)

        if declaration.relation not in created_relations:
            issues.append(
                ContractIssue(
                    relation=declaration.relation,
                    column=declaration.column,
                    problem_type="contract_relation_not_created",
                    message=(
                        f"Relation {declaration.relation!r} has a contract but is not "
                        "created by any manifest step."
                    ),
                    hint="Remove the contract or add the step that creates the relation.",
                )
            )

    for relation, grain_keys in grain_by_relation.items():
        if relation not in by_relation:
            continue

        contract_by_column = {
            item.column: item
            for item in by_relation[relation]
        }

        for grain_key in grain_keys:
            item = contract_by_column.get(grain_key)
            if item is None:
                issues.append(
                    ContractIssue(
                        relation=relation,
                        column=grain_key,
                        problem_type="grain_key_missing_from_contract",
                        message=(
                            f"Grain key {grain_key!r} for relation {relation!r} "
                            "is missing from its relation contract."
                        ),
                        hint="Add the grain key as a contract column.",
                    )
                )
            elif not item.key:
                issues.append(
                    ContractIssue(
                        relation=relation,
                        column=grain_key,
                        problem_type="grain_key_not_marked_key",
                        message=(
                            f"Grain key {grain_key!r} for relation {relation!r} "
                            "is not marked key=true in the relation contract."
                        ),
                        hint="Mark grain columns as key=true.",
                    )
                )

    return issues


def runtime_contract_issues(
    connection: Any,
    relation: str,
    declarations: list[ContractColumn],
) -> list[RuntimeContractIssue]:
    """Check actual relation columns, types, and key uniqueness."""
    expected = [item for item in declarations if item.relation == relation]
    if not expected:
        return []

    quoted_relation = '"' + relation.replace('"', '""') + '"'
    actual_rows = connection.execute(f"DESCRIBE {quoted_relation}").fetchall()
    actual_types = {row[0]: normalize_type(str(row[1])) for row in actual_rows}

    issues: list[RuntimeContractIssue] = []

    for item in expected:
        if item.column not in actual_types:
            issues.append(
                RuntimeContractIssue(
                    relation=relation,
                    column=item.column,
                    problem_type="contract_column_missing",
                    message=f"Expected column {relation}.{item.column} does not exist.",
                    hint="Update the SQL/source relation or the declared contract.",
                )
            )
            continue

        actual_type = actual_types[item.column]
        expected_type = normalize_type(item.data_type)

        if actual_type != expected_type:
            issues.append(
                RuntimeContractIssue(
                    relation=relation,
                    column=item.column,
                    problem_type="contract_type_mismatch",
                    message=(
                        f"{relation}.{item.column} has type {actual_type}, "
                        f"expected {expected_type}."
                    ),
                    hint="Cast the column in SQL or update the expected contract type.",
                )
            )

    key_columns = [item.column for item in expected if item.key]
    if key_columns:
        quoted_keys = ", ".join(
            '"' + name.replace('"', '""') + '"'
            for name in key_columns
        )
        duplicate_count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT {quoted_keys}, COUNT(*) AS n
                FROM {quoted_relation}
                GROUP BY {quoted_keys}
                HAVING COUNT(*) > 1
            ) AS duplicate_keys
            """
        ).fetchone()[0]

        if duplicate_count:
            issues.append(
                RuntimeContractIssue(
                    relation=relation,
                    column=";".join(key_columns),
                    problem_type="contract_key_not_unique",
                    message=(
                        f"Relation {relation!r} violates declared key uniqueness "
                        f"for {', '.join(key_columns)}."
                    ),
                    hint="Fix duplicate rows or revise the declared key.",
                )
            )

    return issues
