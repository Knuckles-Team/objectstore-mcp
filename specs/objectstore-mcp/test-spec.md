# CONN-OBJECTSTORE-MCP — Test specification

Governing spec: [spec.md](spec.md).

| Test ID | Requirement | Proving test | Expected observation |
|---|---|---|---|
| T-001 | `CONN-OBJECTSTORE-MCP-R001` | `tests/test_sdk_backends.py::test_tools_route_through_sdk_backends_and_no_local_copy` (planned) | A filesystem store call returns the object, and no package class defines `backend_type`. |
| T-002 | `CONN-OBJECTSTORE-MCP-R002` | `tests/test_sdk_backends.py::test_extras_name_the_sdk_storage_extras` (planned) | Each extra names one SDK storage extra and no provider library. |
| T-003 | `CONN-OBJECTSTORE-MCP-R003` | `tests/test_sdk_backends.py::test_webdav_store_routes_through_sdk` (planned) | A `webdav` store builds a `WebDavBackend`, and presign returns `STORAGE_UNSUPPORTED`. |
| T-004 | `CONN-OBJECTSTORE-MCP-R004` | `tests/test_sdk_backends.py::test_no_retired_sdk_name_in_package_or_docs` (planned) | 0 matches for the retired name. |
| T-005 | `CONN-OBJECTSTORE-MCP-R002.1` | `tests/test_sdk_backends.py::test_served_image_installs_every_provider_extra` | The `mcp` image target installs `s3`, `gcs` and `azure`. |
| T-006 | `CONN-OBJECTSTORE-MCP-R005` | `tests/test_objectstore_mcp_validation.py::test_tool_inventory_is_typed_with_no_action_routing`, `tests/test_objectstore_mcp_validation.py::test_refusal_keeps_the_storage_cause` | No `action`/`params_json` parameter and no `split-action` tag; refusal names its storage code. |
| T-007 | `CONN-OBJECTSTORE-MCP-R006` | `tests/test_safety.py` | Caps, delete flags, wildcard refusal and dry-run hold on generated and typed tools. |
| T-008 | `CONN-OBJECTSTORE-MCP-R007` | `tests/test_objectstore_mcp_validation.py::test_s3_lifecycle_versioning_and_tags`, `tests/test_objectstore_mcp_validation.py::test_s3_management_refuses_on_filesystem_store` | Lifecycle, versioning and tags round-trip on an S3 client; a filesystem store refuses `STORAGE_UNSUPPORTED`. |
| T-009 | `CONN-OBJECTSTORE-MCP-R008` | `tests/test_surface_ontology.py` | Ontology tools equal served tools; skills, prompt and contracts name served tools; classes subclass core. |

## Negative and boundary cases

A literal credential refuses with `STORAGE_SECRET_LITERAL`. A missing provider library refuses with `STORAGE_DEPENDENCY_MISSING`.

## Quality and release proof

Run `uv run pytest tests` and `pre-commit run --all-files` from the repository root. A planned test is added by the code change that lands the row.
