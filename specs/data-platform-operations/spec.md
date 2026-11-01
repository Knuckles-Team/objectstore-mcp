# CONN-OBJECTSTORE-MCP-DATA-PLATFORM-OPERATIONS — Operations the data-platform vocabulary needs

Owner: objectstore-mcp. Cross-repo IDs: `MEDULLA-DATAPLAT-VOCAB-R009`.

## Purpose and user stories

The medulla data-platform vocabulary answers competency questions from connector facts. One question needs an operation this connector lacks. This spec owns that operation.

## Why a new spec

The existing specs in `specs/` cover packaged content and identity, not tool operations. None owns a new connector operation.

## Scope and interfaces

Owned: the one operation named in the row, touching `objectstore_mcp/mcp/mcp_objectstore.py`. Non-goal: anything in the medulla vocabulary itself.

## Open questions

- None.

## Delivery mapping

Component: objectstore-mcp connector

Code: ../../objectstore_mcp/__init__.py

## User Scenarios & Testing

### User Story 1 - Last-access operation (Priority: P1)

The fleet operator and the engine rely on this behaviour of `objectstore-mcp`: The `objects` tool reports a last-access time, or a typed `unsupported` result for backends without one. It is proven independently of the other stories.

**Acceptance Scenarios**:

1. **Given** the `objectstore-mcp` connector built from the default branch, **When** `tests/test_last_access_operation.py::test_head_and_list_carry_last_accessed_or_unsupported` runs, **Then** a `head`/`list` result carries `last_accessed` or the operation returns typed `unsupported`.

### Edge Cases

- The vendor service is unreachable or rejects the credential: the connector returns the SDK typed error and never a partial result.
- An argument outside the documented inputs is refused with the SDK typed refusal and causes no effect on the vendor service.

## Requirements

- **FR-001**: Last-access operation. Rows: `CONN-OBJECTSTORE-MCP-DATA-PLATFORM-OPERATIONS-R001`.

## Success Criteria

- **SC-001**: a `head`/`list` result carries `last_accessed` or the operation returns typed `unsupported`. Rows: `CONN-OBJECTSTORE-MCP-DATA-PLATFORM-OPERATIONS-R001`.

## Assumptions

- The `objectstore-mcp` package keeps the entry point and module layout named in the rows.
- The shared SDK supplies the transport, authentication, retry and certification helpers the rows reuse.

## Traceability

| Label | Rows | Design section | Test ID | Evidence |
|---|---|---|---|---|
| FR-001 | `CONN-OBJECTSTORE-MCP-DATA-PLATFORM-OPERATIONS-R001` | plan.md Production caller chain | T-001 | tests/test_last_access_operation.py::test_head_and_list_carry_last_accessed_or_unsupported |
