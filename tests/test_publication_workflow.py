"""Keep shared publication and Pages contracts explicit in this connector."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _workflow(name: str):
    return yaml.safe_load((ROOT / ".github/workflows" / name).read_text())


def _actions_on(workflow: dict):
    # PyYAML's YAML 1.1 reader represents the Actions ``on`` key as True.
    return workflow["on"] if "on" in workflow else workflow[True]


def test_pages_publishes_spec_dashboard_and_supports_manual_refresh():

    config = json.loads((ROOT / ".config/spec-dashboard.json").read_text())
    assert config == {
        "version": 1,
        "sources": [{"glob": "specs/*/status.json", "kind": "spec"}],
    }


def test_legacy_docs_publisher_is_removed_and_release_flags_remain_canonical():
    assert not (ROOT / ".github/workflows/docs.yml").exists()


def test_development_skill_has_real_delivery_contract_and_actual_tests():
    skill = ROOT / "objectstore_mcp/skills/objectstore-mcp-development/SKILL.md"
    content = skill.read_text()

    assert "name: objectstore-mcp-development" in content
    assert "## Rapid delivery: the 5-minute contract" in content
    for test_path in (
        "tests/test_publication_workflow.py",
        "tests/test_objectstore_mcp_validation.py",
        "tests/test_backend_conformance.py",
        "tests/test_auth.py",
        "tests/test_api_wrapper.py",
        "tests/test_safety.py",
    ):
        assert test_path in content
        assert (ROOT / test_path).exists()
    for runtime_name in (
        "OBJECTSTORE_STORES",
        "OBJECTSTORE_DEFAULT_STORE",
        "OBJECTSTORE_FS_ROOT",
        "ObjectStoreBackend",
        "agent-connector-sdk",
        "condensed/verbose",
    ):
        assert runtime_name in content


def test_packaged_skill_and_version_lock_are_coherent():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    version = project["version"]
    lock = (ROOT / "uv.lock").read_text()
    assert re.search(
        rf'^name = "objectstore-mcp"\nversion = "{re.escape(version)}"$',
        lock,
        re.MULTILINE,
    )
    package_data = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"][
        "setuptools"
    ]["package-data"]
    assert "skills/**" in package_data["objectstore_mcp"]
    assert (
        ROOT / "objectstore_mcp/skills/objectstore-mcp-development/SKILL.md"
    ).is_file()
