"""Optional deterministic artifact expectations."""

from __future__ import annotations
import csv
from dataclasses import dataclass
from pathlib import Path

ARTIFACT_COLUMNS = ("artifact", "expected")

@dataclass(frozen=True)
class ArtifactExpectation:
    artifact: str
    expected: str

@dataclass(frozen=True)
class ArtifactSpecIssue:
    artifact: str
    problem_type: str
    message: str
    hint: str

def artifact_spec_path(manifest: Path) -> Path:
    return manifest.resolve().parent / "specifications" / "artifacts.csv"

def read_artifact_expectations(manifest: Path):
    path = artifact_spec_path(manifest)
    if not path.exists():
        return [], []

    expectations, issues, seen = [], [], set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        actual = tuple(reader.fieldnames or ())
        if actual != ARTIFACT_COLUMNS:
            return [], [ArtifactSpecIssue(
                "-", "invalid_artifact_spec_header",
                f"Artifact specification header is invalid. Found: {', '.join(actual) or '(none)'}",
                f"Use exactly: {', '.join(ARTIFACT_COLUMNS)}",
            )]

        for line_number, row in enumerate(reader, start=2):
            artifact = (row["artifact"] or "").strip()
            expected = (row["expected"] or "").strip()
            if not artifact or not expected:
                issues.append(ArtifactSpecIssue(
                    artifact or f"line {line_number}",
                    "incomplete_artifact_expectation",
                    "Artifact expectation requires both artifact and expected paths.",
                    "Declare both package-relative paths.",
                ))
                continue
            if artifact in seen:
                issues.append(ArtifactSpecIssue(
                    artifact, "duplicate_artifact_expectation",
                    f"Artifact {artifact!r} is declared more than once.",
                    "Keep one deterministic expectation per artifact.",
                ))
                continue
            seen.add(artifact)
            expectations.append(ArtifactExpectation(artifact, expected))
    return expectations, issues
