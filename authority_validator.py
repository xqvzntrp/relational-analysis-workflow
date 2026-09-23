"""Validate authority-zone dependency direction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dependency_plan import discover_manifest_dependencies


AUTHORITY_ORDER = {
    "source": 0,
    "prepared": 1,
    "review": 2,
    "focused": 3,
    "inform": 4,
    "business": 5,
    "report": 6,
}


@dataclass(frozen=True)
class AuthorityIssue:
    step: str
    authority_zone: str
    relation: str
    producer_step: str
    producer_zone: str
    problem_type: str
    message: str
    hint: str


def validate_authority_progression(manifest: Path) -> list[AuthorityIssue]:
    """Reject dependencies that flow backward across authority zones.

    A step may depend on a relation created in the same authority zone or
    any earlier authority zone. It may not depend on a relation created in
    a later authority zone.
    """
    plan = discover_manifest_dependencies(manifest)

    producers: dict[str, tuple[str, str]] = {}
    issues: list[AuthorityIssue] = []

    for step in plan:
        consumer_rank = AUTHORITY_ORDER[step.authority_zone]

        for relation in step.references:
            producer = producers.get(relation)
            if producer is None:
                # Unresolved relations are handled by dependency validation.
                continue

            producer_step, producer_zone = producer
            producer_rank = AUTHORITY_ORDER[producer_zone]

            if producer_rank > consumer_rank:
                issues.append(
                    AuthorityIssue(
                        step=step.step,
                        authority_zone=step.authority_zone,
                        relation=relation,
                        producer_step=producer_step,
                        producer_zone=producer_zone,
                        problem_type="backward_authority_dependency",
                        message=(
                            f"Relation {relation!r} is produced in later authority "
                            f"zone {producer_zone!r} at step {producer_step}, but "
                            f"step {step.step} is declared as {step.authority_zone!r}."
                        ),
                        hint=(
                            "Move the consuming step to the same or a later authority "
                            "zone, or move the relation's production to an earlier zone."
                        ),
                    )
                )

        for relation in step.creates:
            producers[relation] = (step.step, step.authority_zone)

    return issues
