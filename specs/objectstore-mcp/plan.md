# CONN-OBJECTSTORE-MCP — Implementation plan

Governing spec: [spec.md](spec.md). Rows: [requirements.md](requirements.md).

## Summary

The connector moves its storage backends to the SDK and keeps its tool layer. The live caller is the `objectstore-mcp` console script. Each tool resolves a store, and `get_backend` now builds the backend with the SDK factory. The connector deletes its own backend modules in the same release.

## Technical Context

- **Language/Version**: Python >=3.12 (environment 3.14)
- **Primary Dependencies**: the SDK release with `scion_sdk.storage`; provider libraries through the SDK extras `storage-s3`, `storage-gcs` and `storage-azure`
- **Storage**: N/A, the connector keeps no store of its own
- **Testing**: pytest; each row names the proving test as `path::name`
- **Target Platform**: Linux container and stdio or streamable HTTP MCP clients
- **Project Type**: connector
- **Performance Goals**: N/A, the store sets the latency
- **Constraints**: the connector ships no backend copy; credentials arrive by reference only
- **Scale/Scope**: 9 rows

## Constitution Check

- Organization constitution, spec-first change: pass. Every behavior is a row with a planned test.
- Repository article R-I, connector scope: pass. The shared backends live in the SDK, and the connector reuses them.

## Project Structure

- `objectstore_mcp/auth.py` (existing): `get_backend` calls the SDK factory.
- `objectstore_mcp/config.py` (existing): `parse_stores` replaces the local parser; `Limits` stays.
- `objectstore_mcp/api/__init__.py` (existing): re-exports the SDK names.
- `objectstore_mcp/api/api_client_*.py` (deleted).
- `tests/test_sdk_backends.py` (new, planned).
- `objectstore_mcp/guard.py` (new): the safety governor around every backend (R006).
- `objectstore_mcp/mcp/mcp_objectstore.py` (existing): typed tools only (R005, R007).
- `objectstore_mcp/skills/`, `objectstore_mcp/prompts/`, `objectstore_mcp/ontology/objectstore.ttl` (existing and new content, R008).
- `tests/test_safety.py`, `tests/test_objectstore_mcp_validation.py` (rewritten), `tests/test_surface_ontology.py` (new).

## Phase 0: Research

No unknowns. The SDK rows hold the backend decisions.

## Phase 1: Design

The tool layer keeps its limits; its surface becomes one typed tool per operation (R005), with the limits enforced by a guard around the backend so the SDK-generated tools obey them too (R006). S3-only bucket management reaches the S3 client of an `s3` store (R007). It imports the error and value types from `scion_sdk.storage`. `load_stores` passes the parsed `OBJECTSTORE_STORES` object to `parse_stores` and adds the implicit `local` store. `get_backend` caches one backend per store name and builds it with `create_backend`. The backend tests move to the SDK; the connector keeps one routing test per backend kind.

Store configuration changes in the same release. A store names its secrets in a `credentials` map of references. The `profile` field and the ambient provider credential chain are removed. An operator moves each store to references before the upgrade.

### Adoption of scion-sdk 0.10.0 (CONN-OBJECTSTORE-MCP-R009)

- Owner. This repository, the import lines named in `CONN-OBJECTSTORE-MCP-R009`. The paths belong to scion-sdk.
- Cohesion. The import edits, the pin and the lock change together and sit in one change.
- Dependency direction. The connector imports public modules of the SDK units; no import points to a private module.
- Interface depth. The connector uses the public surface only.
- Special cases. None. Every removed path takes the same replacement, with no alias.
- State. None.
- Environment. None. The pin is package metadata, not environment code.

## Phase 2: Task approach

Pin the SDK first (R002), then switch the backends (R001), then add the WebDAV routing test (R003). R004 has no order.

## Complexity Tracking

None. The constitution check passed.

## Build contract

Gates: `pre-commit run --all-files` and the pre-push stage, then `uv run pytest tests`. No backend class stays in the package, and no provider library is pinned directly.

## Production caller chain

Console script `objectstore-mcp` → `scion_sdk.cli:serve` → the tool functions in `objectstore_mcp/mcp/mcp_objectstore.py` → `get_backend` (objectstore_mcp/auth.py:78) → `create_backend` in `scion_sdk/storage/factory.py`.

## Cross-repo seams

- SDK storage backends: provider `SCION-CENTRALIZED-CAPABILITIES-R042`, consumer `CONN-OBJECTSTORE-MCP-R001`; see [contracts/storage-backends.md](contracts/storage-backends.md).
