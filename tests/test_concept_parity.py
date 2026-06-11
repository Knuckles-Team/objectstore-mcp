"""Every CONCEPT:OBJ-1.x marker in code must be registered in docs/concepts.md."""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MARKER = re.compile(r"CONCEPT:OBJ-1\.\d+")


def collect_code_markers() -> set[str]:
    markers: set[str] = set()
    for path in (REPO / "objectstore_mcp").rglob("*.py"):
        markers.update(MARKER.findall(path.read_text(encoding="utf-8")))
    return markers


def test_code_markers_are_registered_in_docs():
    registry = (REPO / "docs" / "concepts.md").read_text(encoding="utf-8")
    documented = set(MARKER.findall(registry))
    in_code = collect_code_markers()
    assert in_code, "Expected CONCEPT:OBJ-1.x markers in objectstore_mcp/"
    assert in_code <= documented, f"Unregistered concepts: {in_code - documented}"


def test_eco_bridge_and_root_concept_documented():
    registry = (REPO / "docs" / "concepts.md").read_text(encoding="utf-8")
    assert "ECO-4.0" in registry
    assert "CONCEPT:OBJ-1.0" in registry
    assert "CONCEPT:OBJ-1.0" in collect_code_markers()
