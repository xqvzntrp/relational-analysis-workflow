"""Grain-aware package inspection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dependency_plan import discover_manifest_dependencies
from grain_spec import GrainDeclaration, GrainIssue, read_grain_declarations


@dataclass(frozen=True)
class GrainStep:
    step: str
    authority_zone: str
    relation: str
    grain: tuple[str, ...]
    referenced_grains: tuple[tuple[str, tuple[str, ...]], ...]


@dataclass(frozen=True)
class GrainTransition:
    step: str
    authority_zone: str
    relation: str
    grain: tuple[str, ...]
    upstream_relation: str
    upstream_grain: tuple[str, ...]
    changed: bool


@dataclass(frozen=True)
class GrainAnalysis:
    declarations: tuple[GrainDeclaration, ...]
    issues: tuple[GrainIssue, ...]
    steps: tuple[GrainStep, ...]
    transitions: tuple[GrainTransition, ...]


def analyze_grain(manifest: Path) -> GrainAnalysis:
    declarations, issues = read_grain_declarations(manifest)
    grain_by_relation = {item.relation: item.keys for item in declarations}
    plan = discover_manifest_dependencies(manifest)

    steps: list[GrainStep] = []
    transitions: list[GrainTransition] = []

    for item in plan:
        upstream = tuple(
            (relation, grain_by_relation[relation])
            for relation in item.references
            if relation in grain_by_relation
        )

        for created_relation in item.creates:
            declared_grain = grain_by_relation.get(created_relation)
            if declared_grain is None:
                continue

            steps.append(
                GrainStep(
                    step=item.step,
                    authority_zone=item.authority_zone,
                    relation=created_relation,
                    grain=declared_grain,
                    referenced_grains=upstream,
                )
            )

            for upstream_relation, upstream_grain in upstream:
                transitions.append(
                    GrainTransition(
                        step=item.step,
                        authority_zone=item.authority_zone,
                        relation=created_relation,
                        grain=declared_grain,
                        upstream_relation=upstream_relation,
                        upstream_grain=upstream_grain,
                        changed=declared_grain != upstream_grain,
                    )
                )

    return GrainAnalysis(
        declarations=tuple(declarations),
        issues=tuple(issues),
        steps=tuple(steps),
        transitions=tuple(transitions),
    )
