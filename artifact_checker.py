"""Deterministic artifact comparison and readable CSV differences."""

from __future__ import annotations
import csv
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from artifact_spec import ArtifactExpectation

@dataclass(frozen=True)
class ArtifactCheck:
    artifact: str
    expected: str
    matches: bool
    artifact_sha256: str | None
    expected_sha256: str | None
    summary: str
    details: tuple[str, ...]

def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()

def _rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle))

def _csv_diff(actual: Path, expected: Path, limit: int = 8):
    a, e = _rows(actual), _rows(expected)
    details = []
    for i in range(max(len(a), len(e))):
        ar = a[i] if i < len(a) else None
        er = e[i] if i < len(e) else None
        if ar == er:
            continue
        n = i + 1
        if ar is None:
            details.append(f"row {n}: missing actual row; expected {er!r}")
        elif er is None:
            details.append(f"row {n}: unexpected actual row {ar!r}")
        else:
            details.append(f"row {n}: expected {er!r}; actual {ar!r}")
        if len(details) >= limit:
            details.append("... additional differences omitted")
            break
    return tuple(details)

def check_artifact(package_root: Path, expectation: ArtifactExpectation) -> ArtifactCheck:
    actual = (package_root / expectation.artifact).resolve()
    expected = (package_root / expectation.expected).resolve()

    if not actual.exists():
        return ArtifactCheck(expectation.artifact, expectation.expected, False, None,
            _digest(expected) if expected.exists() else None,
            "generated artifact is missing", ())
    if not expected.exists():
        return ArtifactCheck(expectation.artifact, expectation.expected, False, _digest(actual),
            None, "expected artifact is missing", ())

    ah, eh = _digest(actual), _digest(expected)
    if ah == eh:
        return ArtifactCheck(expectation.artifact, expectation.expected, True, ah, eh,
            "artifact matches expected bytes", ())

    details = ()
    if actual.suffix.lower() == ".csv" and expected.suffix.lower() == ".csv":
        details = _csv_diff(actual, expected)
    return ArtifactCheck(expectation.artifact, expectation.expected, False, ah, eh,
        "artifact differs from expected output", details)

def check_expected_artifacts(manifest: Path, expectations: list[ArtifactExpectation]):
    root = manifest.resolve().parent
    return [check_artifact(root, item) for item in expectations]
