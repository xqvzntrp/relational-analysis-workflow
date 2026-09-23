"""Summarize a manifest package for dry-run inspection."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from dependency_plan import discover_manifest_dependencies
from manifest_inspector import inspect_manifest


@dataclass(frozen=True)
class PackageSummary:
    step_count: int
    mode_counts: dict[str, int]
    authority_zone_counts: dict[str, int]
    created_relations: tuple[str, ...]
    referenced_relations: tuple[str, ...]
    export_outputs: tuple[str, ...]
    final_created_relations: tuple[str, ...]


def summarize_package(manifest: Path) -> PackageSummary:
    rows = inspect_manifest(manifest)
    deps = discover_manifest_dependencies(manifest)

    mode_counts = Counter(row.mode for row in rows)
    authority_counts = Counter(row.authority_zone for row in rows)

    created: list[str] = []
    referenced: list[str] = []
    exports: list[str] = []

    for row, dep in zip(rows, deps):
        for relation in dep.creates:
            if relation not in created:
                created.append(relation)
        for relation in dep.references:
            if relation not in referenced:
                referenced.append(relation)
        if row.mode == "export_sql" and row.output_value:
            exports.append(row.output_value)

    consumed = set(referenced)
    final_relations = tuple(
        relation for relation in created if relation not in consumed
    )

    return PackageSummary(
        step_count=len(rows),
        mode_counts=dict(mode_counts),
        authority_zone_counts=dict(authority_counts),
        created_relations=tuple(created),
        referenced_relations=tuple(referenced),
        export_outputs=tuple(exports),
        final_created_relations=final_relations,
    )
