"""Optional relation contracts.

A package may declare expected relation structure in:

    specifications/relation_contract.csv

Strict schema:

    relation,column,data_type,key

Each row declares one expected column.

`key` must be `true` or `false`. Composite keys are represented by marking
multiple columns of the same relation as key=true.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


CONTRACT_COLUMNS = ("relation", "column", "data_type", "key")


@dataclass(frozen=True)
class ContractColumn:
    relation: str
    column: str
    data_type: str
    key: bool


@dataclass(frozen=True)
class ContractIssue:
    relation: str
    column: str
    problem_type: str
    message: str
    hint: str


def contract_spec_path(manifest: Path) -> Path:
    return manifest.resolve().parent / "specifications" / "relation_contract.csv"


def read_relation_contract(
    manifest: Path,
) -> tuple[list[ContractColumn], list[ContractIssue]]:
    """Read optional relation contracts.

    Missing relation_contract.csv is valid and returns no declarations.
    """
    path = contract_spec_path(manifest)
    if not path.exists():
        return [], []

    declarations: list[ContractColumn] = []
    issues: list[ContractIssue] = []

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        actual_columns = tuple(reader.fieldnames or ())

        if actual_columns != CONTRACT_COLUMNS:
            return [], [
                ContractIssue(
                    relation="-",
                    column="-",
                    problem_type="invalid_contract_header",
                    message=(
                        "Relation contract header does not match the required "
                        f"schema. Found: {', '.join(actual_columns) or '(none)'}"
                    ),
                    hint=f"Use exactly: {', '.join(CONTRACT_COLUMNS)}",
                )
            ]

        seen: set[tuple[str, str]] = set()

        for line_number, row in enumerate(reader, start=2):
            relation = (row["relation"] or "").strip()
            column = (row["column"] or "").strip()
            data_type = (row["data_type"] or "").strip().upper()
            raw_key = (row["key"] or "").strip().lower()

            if not relation:
                issues.append(
                    ContractIssue(
                        relation=f"line {line_number}",
                        column=column or "-",
                        problem_type="missing_contract_relation",
                        message="Contract row is missing a relation name.",
                        hint="Declare the relation being described.",
                    )
                )
                continue

            if not column:
                issues.append(
                    ContractIssue(
                        relation=relation,
                        column="-",
                        problem_type="missing_contract_column",
                        message=f"Relation {relation!r} has a contract row without a column name.",
                        hint="Declare the expected column name.",
                    )
                )
                continue

            if not data_type:
                issues.append(
                    ContractIssue(
                        relation=relation,
                        column=column,
                        problem_type="missing_contract_type",
                        message=f"{relation}.{column} has no expected data type.",
                        hint="Declare a DuckDB-compatible type such as VARCHAR, INTEGER, or BOOLEAN.",
                    )
                )
                continue

            if raw_key not in {"true", "false"}:
                issues.append(
                    ContractIssue(
                        relation=relation,
                        column=column,
                        problem_type="invalid_contract_key_flag",
                        message=(
                            f"{relation}.{column} has key={raw_key!r}; expected true or false."
                        ),
                        hint="Use exactly true or false.",
                    )
                )
                continue

            identity = (relation, column)
            if identity in seen:
                issues.append(
                    ContractIssue(
                        relation=relation,
                        column=column,
                        problem_type="duplicate_contract_column",
                        message=f"{relation}.{column} appears more than once in the relation contract.",
                        hint="Keep exactly one contract row per relation column.",
                    )
                )
                continue

            seen.add(identity)
            declarations.append(
                ContractColumn(
                    relation=relation,
                    column=column,
                    data_type=data_type,
                    key=(raw_key == "true"),
                )
            )

    return declarations, issues
