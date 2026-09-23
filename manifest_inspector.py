"""Verbose manifest inspection for dry-run diagnostics."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ManifestRowInspection:
    line_number: int
    step: str
    mode: str
    input_value: str
    output_value: str
    authority_zone: str
    resolved_input: str | None
    resolved_output: str | None


def _resolve_relative(base_dir: Path, value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = base_dir / path
    return str(path.resolve())


def inspect_manifest(path: Path) -> list[ManifestRowInspection]:
    """Read a structurally valid manifest and resolve its relative paths."""
    base_dir = path.resolve().parent
    rows: list[ManifestRowInspection] = []

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for line_number, row in enumerate(reader, start=2):
            input_value = (row.get("input") or "").strip()
            output_value = (row.get("output") or "").strip()
            rows.append(
                ManifestRowInspection(
                    line_number=line_number,
                    step=(row.get("step") or "").strip(),
                    mode=(row.get("mode") or "").strip(),
                    input_value=input_value,
                    output_value=output_value,
                    authority_zone=(row.get("authority_zone") or "").strip(),
                    resolved_input=_resolve_relative(base_dir, input_value),
                    resolved_output=_resolve_relative(base_dir, output_value),
                )
            )
    return rows
