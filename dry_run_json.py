"""Machine-readable dry-run document."""

from __future__ import annotations
from pathlib import Path
from typing import Any

from authority_validator import validate_authority_progression
from dependency_plan import discover_manifest_dependencies
from dependency_validator import validate_dependencies
from grain_analysis import analyze_grain
from manifest_inspector import inspect_manifest
from manifest_validator import validate_manifest
from package_summary import summarize_package
from relation_contract import read_relation_contract
from relation_contract_validator import validate_contract_declarations

def _issue(issue: Any) -> dict[str, Any]:
    result = {
        "problem_type": issue.problem_type,
        "message": issue.message,
        "hint": issue.hint,
    }
    for name in ("step","mode","authority_zone","relation","column",
                 "producer_step","producer_zone"):
        value = getattr(issue, name, None)
        if value is not None:
            result[name] = value
    return result

def build_dry_run_document(manifest: Path, *, verbose: bool = False) -> dict[str, Any]:
    manifest = manifest.resolve()
    manifest_issues = validate_manifest(manifest)
    document: dict[str, Any] = {
        "schema_version": 1,
        "manifest": str(manifest),
        "ready": False,
        "issues": {
            "manifest": [_issue(x) for x in manifest_issues],
            "dependency": [],
            "authority_zone": [],
            "relation_contract": [],
        },
    }
    if manifest_issues:
        return document

    dependencies = discover_manifest_dependencies(manifest)
    dependency_issues = validate_dependencies(manifest)
    authority_issues = [] if dependency_issues else validate_authority_progression(manifest)

    contracts, parse_issues = read_relation_contract(manifest)
    contract_issues = parse_issues if parse_issues else validate_contract_declarations(manifest)

    document["issues"]["dependency"] = [_issue(x) for x in dependency_issues]
    document["issues"]["authority_zone"] = [_issue(x) for x in authority_issues]
    document["issues"]["relation_contract"] = [_issue(x) for x in contract_issues]
    document["ready"] = not any(document["issues"].values())

    if verbose:
        rows = inspect_manifest(manifest)
        summary = summarize_package(manifest)
        grain = analyze_grain(manifest)
        document["steps"] = [{
            "step": r.step, "mode": r.mode, "input": r.input_value,
            "output": r.output_value, "authority_zone": r.authority_zone,
        } for r in rows]
        document["dependencies"] = [{
            "step": d.step, "mode": d.mode, "authority_zone": d.authority_zone,
            "creates": list(d.creates), "references": list(d.references),
        } for d in dependencies]
        document["summary"] = {
            "step_count": summary.step_count,
            "mode_counts": summary.mode_counts,
            "authority_zone_counts": summary.authority_zone_counts,
            "created_relations": list(summary.created_relations),
            "referenced_relations": list(summary.referenced_relations),
            "final_created_relations": list(summary.final_created_relations),
            "export_outputs": list(summary.export_outputs),
        }
        document["grain"] = {
            "declarations": [{"relation": x.relation, "keys": list(x.keys)}
                             for x in grain.declarations],
            "issues": [_issue(x) for x in grain.issues],
            "transitions": [{
                "step": x.step, "authority_zone": x.authority_zone,
                "upstream_relation": x.upstream_relation,
                "upstream_grain": list(x.upstream_grain),
                "relation": x.relation, "grain": list(x.grain),
                "changed": x.changed,
            } for x in grain.transitions],
        }
        document["relation_contracts"] = [{
            "relation": x.relation, "column": x.column,
            "data_type": x.data_type, "key": x.key,
        } for x in contracts]
    return document
