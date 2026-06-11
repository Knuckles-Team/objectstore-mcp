# objectstore-mcp — Concept Overview

> **Category**: Integration | **Ecosystem Role**: MCP Server + A2A Agent
> Built on [`agent-utilities`](https://github.com/Knuckles-Team/agent-utilities) — the unified AGI Harness.

## Description

Object storage **API + MCP Server + A2A Agent** — one tool surface over S3 and
S3-compatible stores (MinIO, Cloudflare R2), Google Cloud Storage, Azure Blob
Storage, and a zero-infra local-filesystem backend. Safety caps, explicit
buckets, and dry-run-by-default batch deletes are enforced uniformly in the
tool layer.

## Architecture

This project follows the standardized agent-package pattern:

- **Modular Design**: split into `api/` (provider client modules implementing
  the `ObjectStoreBackend` protocol) and `mcp/` (action-routed tool modules)
  for cleaner organization.
- **Dynamic Tool Registration**: action-routed dynamic tool tags, strictly
  lowercase, each togglable with a `*TOOL` environment flag (`OBJECTSTORETOOL`).
- **A2A Agent Server**: a Pydantic-AI graph agent (console script
  `objectstore-agent`) that calls the MCP tool surface and exposes an AG-UI
  web interface.
- **Named-store registry**: `OBJECTSTORE_STORES` JSON maps store names to
  backends; the zero-infra `local` filesystem store always exists.

## Concept Registry

This project implements or inherits the following ecosystem concepts:

| Concept ID | Description | Source |
|:-----------|:------------|:-------|
| ECO-4.1 | MCP & Universal Skills | `agent-utilities` (inherited) |
| ECO-4.2 | A2A Network & Consensus | `agent-utilities` (inherited) |
| CONCEPT:OBJ-1.0 | Multi-backend store abstraction | [`concepts.md`](concepts.md) |
| CONCEPT:OBJ-1.3 | Safety governor | [`concepts.md`](concepts.md) |

> 📖 **Full Registry**: See [`agent-utilities/docs/overview.md`](https://github.com/Knuckles-Team/agent-utilities/blob/main/docs/overview.md) for the complete 5-Pillar concept index.
