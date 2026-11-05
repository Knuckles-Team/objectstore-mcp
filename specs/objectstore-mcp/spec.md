# CONN-OBJECTSTORE-MCP — Object storage connector backends

Owner: objectstore-mcp. Cross-repo IDs: `SCION-CENTRALIZED-CAPABILITIES-R042`, `SCION-CENTRALIZED-CAPABILITIES-R042.5`, `SCION-CENTRALIZED-CAPABILITIES-R042.6`.

## Purpose and user stories

The connector serves object-store tools over named stores. The SDK now owns the storage backends, so the connector must use them and keep no copy. This spec owns that cutover, the store configuration the connector reads, and the retired SDK name in its documents.

## Why a new spec

The existing specs cover packaged content and one data-platform operation. No spec owns the connector's backends or its store configuration. This spec owns them.

## Scope and interfaces

Owned: `objectstore_mcp/auth.py`, `objectstore_mcp/config.py`, `objectstore_mcp/api/`, `pyproject.toml` and the documents that name the SDK. Provider: the SDK storage backends of `SCION-CENTRALIZED-CAPABILITIES-R042`; see [contracts/storage-backends.md](contracts/storage-backends.md). Non-goal: the tool names and schemas, which stay unchanged.

## Open questions

- None.

## Delivery mapping

Component: objectstore-mcp connector

Code: ../../objectstore_mcp/auth.py ../../objectstore_mcp/config.py

## User Scenarios & Testing

### User Story 1 - Serve every store through the SDK backends (Priority: P1)

An operator configures named stores. Each tool call reaches the store through the SDK backend, and the connector ships no backend code.

**Acceptance Scenarios**:

1. **Given** an S3-compatible store in `OBJECTSTORE_STORES`, **When** a client lists objects, **Then** the call runs through `scion_sdk.storage.S3Backend`.
2. **Given** the installed package, **When** a reviewer searches it, **Then** no module under `objectstore_mcp/api/` defines a backend.

### User Story 2 - Reach a WebDAV file share as a store (Priority: P2)

An operator adds a store with backend `webdav`. The object tools then read and write that file share.

**Acceptance Scenarios**:

1. **Given** a `webdav` store with credential references, **When** a client puts an object, **Then** the SDK WebDAV backend sends the request.

### Edge Cases

- A store credential written as a literal refuses at load with `STORAGE_SECRET_LITERAL`.
- A store with an ambient provider profile and no credential references refuses with `STORAGE_CONFIG_INVALID`.
- A missing provider library refuses with `STORAGE_DEPENDENCY_MISSING`, and the message names the connector extra.

## Requirements

- **FR-001**: The connector serves every store through the SDK backends and holds no backend copy. Rows: `CONN-OBJECTSTORE-MCP-R001`, `CONN-OBJECTSTORE-MCP-R002`.
- **FR-002**: The connector accepts WebDAV stores. Rows: `CONN-OBJECTSTORE-MCP-R003`.
- **FR-003**: No package file or document names the retired SDK name. Rows: `CONN-OBJECTSTORE-MCP-R004`.

## Success Criteria

- **SC-001**: The full test suite passes with `objectstore_mcp/api/` holding no backend module. Rows: `CONN-OBJECTSTORE-MCP-R001`.
- **SC-002**: A search for the retired SDK name over the package and `docs/` returns 0 matches. Rows: `CONN-OBJECTSTORE-MCP-R004`.

## Assumptions

- The SDK release that carries `SCION-CENTRALIZED-CAPABILITIES-R042` is published before this connector releases.
- The tool layer keeps its own size limits and delete flags.

## Traceability

| Label | Rows | Design section | Test ID | Evidence |
|---|---|---|---|---|
| FR-001 | `CONN-OBJECTSTORE-MCP-R001`, `CONN-OBJECTSTORE-MCP-R002` | plan.md Phase 1 | T-001, T-002 | planned |
| FR-002 | `CONN-OBJECTSTORE-MCP-R003` | plan.md Phase 1 | T-003 | planned |
| FR-003 | `CONN-OBJECTSTORE-MCP-R004` | plan.md Phase 1 | T-004 | planned |
