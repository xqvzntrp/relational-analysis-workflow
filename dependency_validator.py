"""Validate relation dependencies before package execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dependency_plan import StepDependency, discover_manifest_dependencies


@dataclass(frozen=True)
class DependencyIssue:
    step: str
    authority_zone: str
    relation: str
    problem_type: str
    message: str
    hint: str


def validate_dependencies(manifest: Path) -> list[DependencyIssue]:
    """Validate that referenced relations are created by earlier steps."""
    plan = discover_manifest_dependencies(manifest)

    available: set[str] = set()
    issues: list[DependencyIssue] = []

    for step in plan:
        for relation in step.references:
            if relation not in available:
                issues.append(
                    DependencyIssue(
                        step=step.step,
                        authority_zone=step.authority_zone,
                        relation=relation,
                        problem_type="unresolved_relation",
                        message=(
                            f"Relation {relation!r} is referenced before any "
                            "earlier manifest step creates it."
                        ),
                        hint=(
                            "Add or move the step that creates this relation "
                            "so it appears earlier in the manifest."
                        ),
                    )
                )

        available.update(step.creates)

    return issues
