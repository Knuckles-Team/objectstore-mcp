# CONN-OBJECTSTORE-MCP-DATA-PLATFORM-OPERATIONS — Test specification

Governing spec: [spec.md](spec.md).

| Test ID | Requirement | Level | Setup and input | Expected observation | Evidence |
|---|---|---|---|---|---|
| T-001 | CONN-OBJECTSTORE-MCP-DATA-PLATFORM-OPERATIONS-R001 | Contract | A fixture backend | a `head`/`list` result carries `last_accessed` or the operation returns typed `unsupported`. |  |

## Negative and boundary cases

A backend without the capability returns a typed unsupported result.

## Quality and release proof

Run the focused test with `uv run pytest` on the new test file.
