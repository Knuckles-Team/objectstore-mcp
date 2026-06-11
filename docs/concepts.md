# Concept Registry — objectstore-mcp

> **Prefix**: `CONCEPT:OBJ-*`

Stable concept IDs trace the connector's core ideas across documentation,
code docstrings, and tests.

| Concept ID | Name | Description |
|---|---|---|
| `CONCEPT:OBJ-1.0` | Multi-Backend Store Abstraction | The `ObjectStoreBackend` protocol in `backends/base.py`: one bucket-agnostic contract every provider implements, validated by a single conformance suite (`tests/test_backend_conformance.py`) |
| `CONCEPT:OBJ-1.1` | Named-Store Registry | `OBJECTSTORE_STORES` JSON maps store names to backend + connection settings; `auth.get_backend()` resolves and caches them; the zero-infra `local` store always exists |
| `CONCEPT:OBJ-1.2` | Action-Routed Tool Surface | Three consolidated MCP tools (`objects`, `buckets`, `transfer`) that route an `action` + `params_json` + optional `store` to the backend |
| `CONCEPT:OBJ-1.3` | Safety Governor | Tool-layer enforcement of size caps, list/batch key caps, explicit-bucket+key deletes (no wildcards), dry-run-by-default batch deletes, and opt-in empty-only bucket deletes |
| `CONCEPT:OBJ-1.4` | Zero-Infra Filesystem Backend | `FilesystemBackend`: buckets as directories, metadata sidecars under `.meta/`, full protocol coverage with no cloud dependencies |
| `CONCEPT:OBJ-1.5` | Optional-Dependency Cloud Backends | S3/GCS/Azure adapters import their SDKs lazily; a missing SDK raises `MissingDependencyError` naming the pip extra (`s3`, `gcs`, `azure`) |
