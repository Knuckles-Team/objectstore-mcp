# CONN-OBJECTSTORE-MCP-DATA-PLATFORM-OPERATIONS — Requirements

Governing spec: [spec.md](spec.md).

Each row is one requirement. A row names the file it touches and the test that proves it. The generator sets each row's state in `status.json`.

| ID | Requirement | Acceptance |
|---|---|---|
| `CONN-OBJECTSTORE-MCP-DATA-PLATFORM-OPERATIONS-R001` | **Last-access operation.** The `objects` tool reports a last-access time, or a typed `unsupported` result for backends without one. Touches `objectstore_mcp/mcp/mcp_objectstore.py`. Moved from `MEDULLA-DATAPLAT-VOCAB-R009.1` (medulla). | a `head`/`list` result carries `last_accessed` or the operation returns typed `unsupported`. |
