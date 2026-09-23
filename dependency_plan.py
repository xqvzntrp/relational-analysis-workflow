"""Build a dependency description for a manifest package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dependency_discovery import SqlDependencies, discover_sql_dependencies
from manifest_inspector import inspect_manifest


@dataclass(frozen=True)
class StepDependency:
    step: str
    mode: str
    authority_zone: str
    creates: tuple[str, ...]
    references: tuple[str, ...]


def discover_manifest_dependencies(manifest: Path) -> list[StepDependency]:
    """Return best-effort created/referenced relations for each step."""
    rows = inspect_manifest(manifest)
    dependencies: list[StepDependency] = []

    for row in rows:
        creates: tuple[str, ...] = ()
        references: tuple[str, ...] = ()

        if row.mode == "load_csv":
            if row.output_value:
                creates = (row.output_value,)

        elif row.mode == "run_sql":
            sql_path = Path(row.resolved_input or "")
            sql_deps = discover_sql_dependencies(sql_path)
            creates = sql_deps.creates
            references = sql_deps.references

        elif row.mode == "export_sql":
            source = row.input_value.strip()
            lowered = source.lower()

            if lowered.startswith("select ") or lowered.startswith("with "):
                # Best-effort extraction from inline query text.
                temp_path = manifest.resolve().parent / ".dependency_inline.sql"
                try:
                    temp_path.write_text(source, encoding="utf-8")
                    sql_deps = discover_sql_dependencies(temp_path)
                    references = sql_deps.references
                finally:
                    temp_path.unlink(missing_ok=True)
            elif source:
                references = (source,)

        dependencies.append(
            StepDependency(
                step=row.step,
                mode=row.mode,
                authority_zone=row.authority_zone,
                creates=creates,
                references=references,
            )
        )

    return dependencies
