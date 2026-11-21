# CONN-OBJECTSTORE-MCP-CONNECTOR-CONTENT — Requirements

Governing spec: [spec.md](spec.md).

Each row is one requirement. A row names the file it touches and the test that proves it. The generator sets each row's state in `status.json`.

| ID | Requirement | Acceptance |
|---|---|---|
| `CONN-OBJECTSTORE-MCP-CONNECTOR-CONTENT-R001` | **Default content.** `pyproject.toml` declares `objectstore-mcp` as the single `scion_sdk.connector` entry point. The server lists the packaged `skill://` and `ontology://` resources and the packaged prompts with no `content=` argument. Caller chain: `objectstore-mcp` in `pyproject.toml` runs `scion_sdk.cli:serve`, which builds the server from the `scion_sdk.connector` entry point `objectstore_mcp:connector` (`objectstore_mcp/__init__.py:13`); the SDK `Connector` then lists the packaged skills, ontology and prompts. Shape: `pyproject.toml` entry point `objectstore-mcp` plus the `connector = Connector(.)` object in `objectstore_mcp/__init__.py`; the packaged `skills/`, `ontology/` and `prompts/` directories of `objectstore_mcp` are reused as is, with no connector-local registration code. Proving test (planned): `tests/test_default_content_surfaces.py::test_default_content_surfaces`. Proving test (planned): `tests/test_default_content_surfaces.py::test_default_content_surfaces`. Proving test (planned): `tests/test_default_content_surfaces.py::test_default_content_surfaces`. The pack extends only the core ontology: it redeclares no class or property the core already declares and carries no pre-rename IRI base. | `resources/list` includes `skill://` and `ontology://`; `prompts/list` includes each packaged prompt. Also: `tests/test_ontology_one_schema.py::test_pack_declares_no_core_owned_term`. |
