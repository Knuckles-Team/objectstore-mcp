# CONN-OBJECTSTORE-MCP — Object storage connector backends

Owner: objectstore-mcp. Cross-repo IDs: `SCION-CENTRALIZED-CAPABILITIES-R042`, `SCION-CENTRALIZED-CAPABILITIES-R042.5`, `SCION-CENTRALIZED-CAPABILITIES-R042.6`.

## Purpose and user stories

The connector serves object-store tools over named stores. The SDK now owns the storage backends, so the connector must use them and keep no copy. This spec owns that cutover, the store configuration the connector reads, and the retired SDK name in its documents.

## Why a new spec

The existing specs cover packaged content and one data-platform operation. No spec owns the connector's backends or its store configuration. This spec owns them.

## Scope and interfaces

Owned: `objectstore_mcp/auth.py`, `objectstore_mcp/config.py`, `objectstore_mcp/guard.py`, `objectstore_mcp/api/`, `objectstore_mcp/mcp/mcp_objectstore.py`, the packaged skills, prompt and ontology, `pyproject.toml` and the documents that name the SDK. Provider: the SDK storage backends of `SCION-CENTRALIZED-CAPABILITIES-R042`; see [contracts/storage-backends.md](contracts/storage-backends.md). The tool surface is one typed tool per operation (R005).

## Open questions

- None.

## Delivery mapping

Component: objectstore-mcp connector

Code: ../../objectstore_mcp/auth.py ../../objectstore_mcp/config.py ../../objectstore_mcp/guard.py ../../objectstore_mcp/mcp/mcp_objectstore.py

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

### User Story 3 - Serve a typed, governed tool surface (Priority: P1)

An agent calls one typed tool per operation, through the fleet gateway, and every tool applies the same caps and delete guards. A refusal names its cause.

**Acceptance Scenarios**:

1. **Given** the served server, **When** a client lists tools, **Then** no tool takes `action` or `params_json`.
2. **Given** an `s3` store whose endpoint is not in `allowed_private_hosts`, **When** a tool runs, **Then** the error reads `STORAGE_EGRESS_REFUSED`.

### User Story 4 - Run the business asset store (Priority: P1)

The business keeps its media in the object store: generated creative outputs, video masters and social-media uploads. An agent provisions the buckets with versioning and retention, tags each asset's stage, and hands it on by presigned URL.

**Acceptance Scenarios**:

1. **Given** an `s3` store, **When** the agent puts a lifecycle rule and reads it back, **Then** the same rule returns.
2. **Given** an asset, **When** the agent follows the `objectstore-business-asset-store` skill, **Then** every tool it names is served.

### Edge Cases

- A store credential written as a literal refuses at load with `STORAGE_SECRET_LITERAL`.
- A store with an ambient provider profile and no credential references refuses with `STORAGE_CONFIG_INVALID`.
- A missing provider library refuses with `STORAGE_DEPENDENCY_MISSING`, and the message names the connector extra.

## Requirements

- **FR-001**: The connector serves every store through the SDK backends and holds no backend copy. Rows: `CONN-OBJECTSTORE-MCP-R001`, `CONN-OBJECTSTORE-MCP-R002`.
- **FR-002**: The connector accepts WebDAV stores. Rows: `CONN-OBJECTSTORE-MCP-R003`.
- **FR-003**: No package file or document names the retired SDK name. Rows: `CONN-OBJECTSTORE-MCP-R004`.
- **FR-004**: The served image carries every provider library. Rows: `CONN-OBJECTSTORE-MCP-R002.1`.
- **FR-005**: The tool surface is typed, governed and names refusal causes. Rows: `CONN-OBJECTSTORE-MCP-R005`, `CONN-OBJECTSTORE-MCP-R006`.
- **FR-006**: S3 lifecycle, versioning and object tags are served. Rows: `CONN-OBJECTSTORE-MCP-R007`.
- **FR-007**: Skills, the business prompt and the ontology describe the served surface. Rows: `CONN-OBJECTSTORE-MCP-R008`.

## Success Criteria

- **SC-001**: The full test suite passes with `objectstore_mcp/api/` holding no backend module. Rows: `CONN-OBJECTSTORE-MCP-R001`.
- **SC-002**: A search for the retired SDK name over the package and `docs/` returns 0 matches. Rows: `CONN-OBJECTSTORE-MCP-R004`.

## Assumptions

- The SDK release that carries `SCION-CENTRALIZED-CAPABILITIES-R042` is published before this connector releases.
- The tool layer keeps its own size limits and delete flags, enforced by the guard on every tool.

## Traceability

| Label | Rows | Design section | Test ID | Evidence |
|---|---|---|---|---|
| FR-001 | `CONN-OBJECTSTORE-MCP-R001`, `CONN-OBJECTSTORE-MCP-R002` | plan.md Phase 1 | T-001, T-002 | planned |
| FR-002 | `CONN-OBJECTSTORE-MCP-R003` | plan.md Phase 1 | T-003 | planned |
| FR-003 | `CONN-OBJECTSTORE-MCP-R004` | plan.md Phase 1 | T-004 | planned |
| FR-004 | `CONN-OBJECTSTORE-MCP-R002.1` | plan.md Phase 1 | T-005 | bound |
| FR-005 | `CONN-OBJECTSTORE-MCP-R005`, `CONN-OBJECTSTORE-MCP-R006` | plan.md Phase 1 | T-006, T-007 | bound |
| FR-006 | `CONN-OBJECTSTORE-MCP-R007` | plan.md Phase 1 | T-008 | bound |
| FR-007 | `CONN-OBJECTSTORE-MCP-R008` | plan.md Phase 1 | T-009 | bound |
