"""CONN-OBJECTSTORE-MCP-R008: the packaged surface (skills, prompt, ontology) matches the served tools."""

import json
import re
from pathlib import Path

import pytest
from fastmcp import Client

PKG = Path(__file__).resolve().parent.parent / "objectstore_mcp"
TTL = (PKG / "ontology" / "objectstore.ttl").read_text(encoding="utf-8")


async def _served(mcp) -> set[str]:
    async with Client(mcp) as client:
        return {t.name for t in await client.list_tools()}


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R008")
async def test_every_served_tool_is_an_ontology_tool_and_no_other(mcp):
    declared = set(re.findall(r'^:tool_(\w+) a :Tool', TTL, flags=re.M))
    assert declared == await _served(mcp)


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R008")
async def test_skills_prompt_and_contracts_name_served_tools(mcp):
    served = await _served(mcp)
    skills = {p.parent.name for p in (PKG / "skills").glob("*/SKILL.md")}
    for name in re.findall(r'^:skill_\w+ a :Skill ;\n    rdfs:label "([\w-]+)"', TTL, flags=re.M):
        assert name in skills
    for skill in skills:
        body = (PKG / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        for tool in set(re.findall(r"`(objectstore_[a-z_]+)`", body)):
            assert tool in served, (skill, tool)
        assert "params_json" not in body and "action=" not in body, skill
    prompt = json.loads((PKG / "prompts" / "objectstore_asset_librarian.json").read_text())
    agent = prompt["agent"]
    assert set(agent["tools"]) <= served
    assert set(agent["guardrails"]["approval_required"]) <= served
    assert set(agent["skills"]) <= skills
    for tool in re.findall(r":usesTool :tool_(\w+)", TTL):
        assert tool in served


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R008")
def test_classes_roll_up_to_core_by_subclass_never_import():
    assert "owl:imports" not in TTL
    for cls, parent in (("ObjectStore", "StorageContainer"), ("Bucket", "StorageContainer"), ("Object", "File")):
        block = TTL.split(f":{cls} a owl:Class ;", 1)[1].split("\n\n", 1)[0]
        assert f"rdfs:subClassOf :{parent}" in block, cls
