# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
