"""Declarative contract for package manifests.

This module defines the manifest shape but does not validate files yet.
Validation is intentionally deferred to a later commit.
"""

MANIFEST_COLUMNS = (
    "step",
    "mode",
    "input",
    "output",
    "authority_zone",
)

MODES = (
    "load_csv",
    "run_sql",
    "export_sql",
)

AUTHORITY_ZONES = (
    "source",
    "prepared",
    "review",
    "focused",
    "inform",
    "business",
    "report",
)
