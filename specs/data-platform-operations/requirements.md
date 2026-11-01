# CONN-OBJECTSTORE-MCP-DATA-PLATFORM-OPERATIONS — Requirements

Governing spec: [spec.md](spec.md).

Each row is one requirement. A row names the file it touches and the test that proves it. The generator sets each row's state in `status.json`.

| ID | Requirement | Acceptance |
|---|---|---|
| `CONN-OBJECTSTORE-MCP-DATA-PLATFORM-OPERATIONS-R001` | **Last-access operation.** The `objects` tool reports a last-access time, or a typed `unsupported` result for backends without one. Touches `objectstore_mcp/mcp/mcp_objectstore.py`. Moved from `MEDULLA-DATAPLAT-VOCAB-R009.1` (medulla). Caller chain: arbora `fleet.call` reaches the `objects` tool (objectstore_mcp/mcp/mcp_objectstore.py:103), which calls the S3 client of `objectstore_mcp/api/api_client_s3.py`. Shape: a `last_accessed` field on `head` and `list` results from the backend, or a typed `unsupported` result; extends the existing `LastModified` mapping in `objectstore_mcp/api/api_client_s3.py`. Proving test (planned): `tests/test_last_access_operation.py::test_head_and_list_carry_last_accessed_or_unsupported`. | a `head`/`list` result carries `last_accessed` or the operation returns typed `unsupported`. |
