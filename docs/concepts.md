# Concept Registry — objectstore-mcp

> **Prefix**: `CONCEPT:OBJ-*` | **Version**: 0.1.0

This connector inherits the ecosystem bridge concept `ECO-4.0`
(connector parity standard) from
[`scion-sdk`](https://github.com/Knuckles-Team/scion-sdk/blob/main/docs/overview.md),
alongside `ECO-4.1` (MCP & Universal Skills) and `AU-ECO.toolkit.journey-map-narrative` (A2A Network).

Stable concept IDs trace the connector's core ideas across documentation,
code docstrings, and tests.

| Concept ID | Name | Description |
|---|---|---|
| `CONCEPT:OB-OS.governance.every-provider-implements-same` | Multi-Backend Store Abstraction | The SDK `ObjectStoreBackend` protocol (`scion_sdk.storage`): one bucket-agnostic contract every provider implements; the SDK conformance suite validates it |
| `CONCEPT:OB-OS.config.obj` | Named-Store Registry | `OBJECTSTORE_STORES` JSON maps store names to backend + connection settings; `auth.get_backend()` resolves and caches them; the zero-infra `local` store always exists |
| `CONCEPT:OB-OS.governance.obj-2` | Typed Tool Surface | One typed MCP tool per operation: the SDK generates the backend-protocol tools, the connector adds composite, transfer, S3-management and ingest tools, each with an optional `store` |
| `CONCEPT:OB-OS.safety.size-caps-list-batch` | Safety Governor | Tool-layer enforcement of size caps, list/batch key caps, explicit-bucket+key deletes (no wildcards), dry-run-by-default batch deletes, and opt-in empty-only bucket deletes |
| `CONCEPT:OB-OS.governance.zero-infra-default` | Zero-Infra Filesystem Backend | `FilesystemBackend`: buckets as directories, metadata sidecars under `.meta/`, full protocol coverage with no cloud dependencies |
| `CONCEPT:OB-OS.governance.obj-3` | Optional-Dependency Cloud Backends | S3/GCS/Azure adapters import their SDKs lazily; a missing SDK raises `MissingDependencyError` naming the pip extra (`s3`, `gcs`, `azure`) |
