"""Optional analytical grain declarations.

A package may declare relation grain in:

    specifications/grain.csv

The file is optional and uses the strict schema:

    relation,grain

Composite grain keys are separated with semicolons, for example:

    prepared_product_attribute,product_id;attribute_id
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


GRAIN_COLUMNS = ("relation", "grain")


@dataclass(frozen=True)
class GrainDeclaration:
    relation: str
    keys: tuple[str, ...]


@dataclass(frozen=True)
class GrainIssue:
    relation: str
    problem_type: str
    message: str
    hint: str


def grain_spec_path(manifest: Path) -> Path:
    return manifest.resolve().parent / "specifications" / "grain.csv"


def read_grain_declarations(manifest: Path) -> tuple[list[GrainDeclaration], list[GrainIssue]]:
    """Read optional grain declarations.

    Missing grain.csv is valid and returns no declarations or issues.
    """
    path = grain_spec_path(manifest)
    if not path.exists():
        return [], []

    issues: list[GrainIssue] = []
    declarations: list[GrainDeclaration] = []

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        actual_columns = tuple(reader.fieldnames or ())

        if actual_columns != GRAIN_COLUMNS:
            return [], [
                GrainIssue(
                    relation="-",
                    problem_type="invalid_grain_header",
                    message=(
                        "Grain specification header does not match the required "
                        f"schema. Found: {', '.join(actual_columns) or '(none)'}"
                    ),
                    hint=f"Use exactly: {', '.join(GRAIN_COLUMNS)}",
                )
            ]

        seen_relations: set[str] = set()

        for line_number, row in enumerate(reader, start=2):
            relation = (row["relation"] or "").strip()
            grain = (row["grain"] or "").strip()

            if not relation:
                issues.append(
                    GrainIssue(
                        relation=f"line {line_number}",
                        problem_type="missing_grain_relation",
                        message="Grain declaration is missing a relation name.",
                        hint="Declare the relation whose analytical grain is being described.",
                    )
                )
                continue

            if relation in seen_relations:
                issues.append(
                    GrainIssue(
                        relation=relation,
                        problem_type="duplicate_grain_relation",
                        message=f"Relation {relation!r} has more than one grain declaration.",
                        hint="Keep exactly one grain declaration per relation.",
                    )
                )
                continue

            seen_relations.add(relation)

            keys = tuple(
                key.strip()
                for key in grain.split(";")
                if key.strip()
            )

            if not keys:
                issues.append(
                    GrainIssue(
                        relation=relation,
                        problem_type="empty_grain",
                        message=f"Relation {relation!r} has an empty grain declaration.",
                        hint="Declare at least one grain key, separated by semicolons for composites.",
                    )
                )
                continue

            if len(set(keys)) != len(keys):
                issues.append(
                    GrainIssue(
                        relation=relation,
                        problem_type="duplicate_grain_key",
                        message=f"Relation {relation!r} repeats a grain key.",
                        hint="List each grain key once.",
                    )
                )
                continue

            declarations.append(
                GrainDeclaration(
                    relation=relation,
                    keys=keys,
                )
            )

    return declarations, issues
