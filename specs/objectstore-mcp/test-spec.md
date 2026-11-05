# CONN-OBJECTSTORE-MCP — Test specification

Governing spec: [spec.md](spec.md).

| Test ID | Requirement | Proving test | Expected observation |
|---|---|---|---|
| T-001 | `CONN-OBJECTSTORE-MCP-R001` | `tests/test_sdk_backends.py::test_tools_route_through_sdk_backends_and_no_local_copy` (planned) | A filesystem store call returns the object, and no package class defines `backend_type`. |
| T-002 | `CONN-OBJECTSTORE-MCP-R002` | `tests/test_sdk_backends.py::test_extras_name_the_sdk_storage_extras` (planned) | Each extra names one SDK storage extra and no provider library. |
| T-003 | `CONN-OBJECTSTORE-MCP-R003` | `tests/test_sdk_backends.py::test_webdav_store_routes_through_sdk` (planned) | A `webdav` store builds a `WebDavBackend`, and presign returns `STORAGE_UNSUPPORTED`. |
| T-004 | `CONN-OBJECTSTORE-MCP-R004` | `tests/test_sdk_backends.py::test_no_retired_sdk_name_in_package_or_docs` (planned) | 0 matches for the retired name. |

## Negative and boundary cases

A literal credential refuses with `STORAGE_SECRET_LITERAL`. A missing provider library refuses with `STORAGE_DEPENDENCY_MISSING`.

## Quality and release proof

Run `uv run pytest tests` and `pre-commit run --all-files` from the repository root. A planned test is added by the code change that lands the row.
