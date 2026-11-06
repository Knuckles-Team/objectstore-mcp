# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.1] - 2026-11-06

### Changed
- Surface backfill: 11 tool-use contracts covering all 32 tools, operator and two business-role prompts, data locations, scion-sdk 0.9

## [2.5.0] - 2026-11-06

### Changed
- One typed tool per operation; the action-routed `objects`, `buckets`,
  `transfer` and `objectstore_ingest` tools are removed. New typed tools:
  `objectstore_list_stores`, `objectstore_move_object`,
  `objectstore_delete_objects_by_prefix`, `objectstore_upload_file`,
  `objectstore_download_file`, `objectstore_upload_directory`,
  `objectstore_download_prefix`, `objectstore_ingest_buckets`,
  `objectstore_ingest_objects` (CONN-OBJECTSTORE-MCP-R005).
- Caps and delete guards wrap every tool's backend, including the
  SDK-generated per-operation tools (CONN-OBJECTSTORE-MCP-R006).
- A store refusal keeps its storage code and message (CONN-OBJECTSTORE-MCP-R005).

### Added
- S3 lifecycle rules, bucket versioning and object tags
  (CONN-OBJECTSTORE-MCP-R007).
- The `objectstore-business-asset-store` skill, the Asset Librarian prompt, and
  ontology roll-up, tool, skill, contract and data-location records
  (CONN-OBJECTSTORE-MCP-R008).

### Fixed
- The served image installs the `s3`, `gcs` and `azure` extras; 2.4.0 images
  refused every S3 store with `STORAGE_DEPENDENCY_MISSING`
  (CONN-OBJECTSTORE-MCP-R002.1).

## [2.4.0] - 2026-11-05

### Changed
- Every store runs through the scion-sdk storage backends (`scion_sdk.storage`);
  the connector's own backend modules are removed (CONN-OBJECTSTORE-MCP-R001).
- Store secrets move to a per-store `credentials` map of secret references
  (`env://`, `openbao://`); the `profile` field and the ambient provider
  credential chains are removed. Migrate each store before upgrading.
- Extras `s3`, `gcs`, `azure` install the SDK extras `storage-s3`, `storage-gcs`,
  `storage-azure` (CONN-OBJECTSTORE-MCP-R002). Requires `scion-sdk>=0.8.0,<0.9`.

### Added
- WebDAV stores (`"backend": "webdav"`) through the SDK WebDAV backend
  (CONN-OBJECTSTORE-MCP-R003).

### Fixed
- Documents name the SDK by its current name (CONN-OBJECTSTORE-MCP-R004).

## [2.3.8] - 2026-10-30

### Changed
- Require `scion-sdk>=0.6.4,<0.7.0`; `uv.lock` relocked.

## [2.3.6] - 2026-10-26

### Added
- Adopt the canonical spec-delivery Pages dashboard and package the
  objectstore-mcp development skill.

## [2.3.5] - 2026-10-24

### Changed
- Central connector migration: requires `agent-connector-sdk>=0.5.4`; server bootstrap, version, containers, ontology artifacts, security scaffold and pre-commit config are provided centrally.

## [2.3.4] - 2026-10-23

### Changed
- Requires `agent-connector-sdk>=0.4.1`; data sources are declared in code (`connector_sources`).

## [Unreleased]

## [0.1.0] - 2026-06-11
### Added
- Multi-backend object-store abstraction (`ObjectStoreBackend` protocol,
  CONCEPT:OBJ-1.0) with four implementations: local filesystem (zero-infra
  default), S3/S3-compatible (MinIO, Cloudflare R2), Google Cloud Storage,
  and Azure Blob Storage.
- Three consolidated, action-routed MCP tools: `objects` (list/head/get/put/
  copy/move/delete/delete_batch/presign/metadata_get/metadata_set), `buckets`
  (list/create/delete/exists/info/stores), and `transfer` (upload/download/
  upload_dir/download_prefix).
- Named multi-store routing via `OBJECTSTORE_STORES` JSON with a built-in
  `local` filesystem store and `OBJECTSTORE_DEFAULT_STORE` selection.
- Safety governor: size caps on get/put/transfer, list/batch key caps,
  explicit-bucket+key deletes with wildcard rejection, prefix-scoped batch
  deletes that dry-run by default, and opt-in empty-only bucket deletes.
- Optional-dependency extras (`s3`, `gcs`, `azure`, `all`, `test`, `test-s3`)
  with graceful `MissingDependencyError` guidance when an SDK is absent.
- Protocol-conformance test suite run for real against the filesystem
  backend, fake-client translation tests for S3/GCS/Azure, optional moto
  integration tests, and end-to-end FastMCP tool tests.
- Dockerfile, compose files, docs (architecture/usage/concepts), and the
  fleet-standard AGENTS/CLAUDE/pre-commit scaffolding.
