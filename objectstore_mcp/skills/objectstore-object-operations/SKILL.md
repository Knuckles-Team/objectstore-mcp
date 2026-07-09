---
name: objectstore-object-operations
skill_type: skill
description: >-
  Object-level operations on S3/MinIO/R2, Google Cloud Storage, Azure Blob, and a
  local filesystem store via the objectstore-mcp MCP server — list, head, get, put,
  copy, move, delete, presign, and tag objects with the single action-routed
  `objects` tool. Use when the agent must read or write an object's bytes/metadata,
  page through a bucket by prefix, mint a presigned URL, or delete objects. Do NOT
  use for creating/deleting buckets (use objectstore-bucket-administration) or moving
  whole files/directories to and from local disk (use objectstore-data-transfer).
license: MIT
tags: [objectstore, s3, gcs, azure-blob, minio, objects, mcp]
metadata:
  author: Genius
  version: '0.1.0'
---
# ObjectStore Object Operations

Uniform object-level access across every backend the objectstore-mcp server fronts
(S3/MinIO/R2, GCS, Azure Blob, local filesystem). One action-routed tool, `objects`,
carries the safety caps and encoding rules so backends stay pure storage adapters.

## When to use
- List objects under a prefix (optionally folding at a `/` delimiter), with paging.
- HEAD/stat a single object, or GET its bytes (size-capped, text or base64).
- PUT an object from text or base64, optionally with `content_type` + `metadata`.
- Copy/move an object, mint a presigned URL, or get/set an object's user metadata.
- Delete a single object, or `delete_batch` a prefix (dry-run first).

## When NOT to use
- Create/delete/inspect buckets or list configured stores →
  `objectstore-bucket-administration`.
- Upload/download local files or whole directories/prefixes to disk →
  `objectstore-data-transfer`.
- Mirror object/bucket metadata into the knowledge graph → the `objectstore_ingest`
  tool (see **Related**).

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`objectstore-mcp`** MCP server.
Stores come from `OBJECTSTORE_STORES` (JSON); a zero-infra `local` filesystem store
always exists. Credentials resolve through each provider's own chain — none are read
by the server.

| Variable | Required | Notes |
|----------|----------|-------|
| `OBJECTSTORE_STORES` | optional | JSON map of named stores → backend + settings |
| `OBJECTSTORE_DEFAULT_STORE` | optional | Store used when `store` is omitted |
| `OBJECTSTORE_FS_ROOT` | optional | Root for the always-on `local` store |
| `OBJECTSTORE_MAX_GET_BYTES` / `OBJECTSTORE_MAX_PUT_BYTES` | optional | Read/write size caps |
| `OBJECTSTORE_MAX_LIST_KEYS` / `OBJECTSTORE_MAX_BATCH_KEYS` | optional | List/batch caps |
| `OBJECTSTORE_ALLOW_DELETE` | optional | Master switch for object deletes (default true) |
| S3: `AWS_*` / profile · GCS: `GOOGLE_APPLICATION_CREDENTIALS` · Azure: `AZURE_STORAGE_CONNECTION_STRING` | per-backend | Provider SDK credential chains |

## Tools & actions
| Tool | Actions |
|------|---------|
| `objects` | `list`, `head`, `get`, `put`, `copy`, `move`, `delete`, `delete_batch`, `presign`, `metadata_get`, `metadata_set` |

Each call takes `action`, a `params_json` **JSON string**, and optional `store`.

### Key parameters
- `bucket` — target bucket (falls back to the store's default bucket for reads/writes,
  but NOT for deletes).
- `key` — object key. `get` also takes `mode` (`auto`|`text`|`base64`) and `max_bytes`.
- `put` — `text` OR `content_base64` (not both), plus optional `content_type`,
  `metadata`.
- `copy`/`move` — `dest_bucket` (defaults to `bucket`) + `dest_key`.
- `delete` — requires explicit `bucket` AND `key`, no wildcards.
- `delete_batch` — explicit `bucket` + non-empty `prefix`, `dry_run` defaults `true`.

## Recipes (`params_json`)
List a prefix, folding at `/`:
```json
{"bucket":"media-prod","prefix":"logs/","delimiter":"/","max_keys":100}
```
Get an object as text:
```json
{"bucket":"media-prod","key":"logs/app.log","mode":"text","max_bytes":1048576}
```
Put a small JSON object with a content type:
```json
{"bucket":"media-prod","key":"config/app.json","text":"{\"on\":true}","content_type":"application/json"}
```
Dry-run a prefix delete before committing:
```json
{"bucket":"media-prod","prefix":"tmp/","max_keys":50,"dry_run":true}
```

## Gotchas
- `params_json` is a **string** of JSON, not an object — serialize it.
- `delete` needs an explicit `bucket` AND `key` with no `*`/`?`; store default buckets
  do not apply to deletes. Use `delete_batch` for prefixes.
- `delete_batch` is `dry_run:true` by default and returns the matched keys — review
  them, then re-send with `dry_run:false`.
- `get`/`put` are size-capped (`OBJECTSTORE_MAX_GET_BYTES`/`_PUT_BYTES`); large payloads
  belong to `objectstore-data-transfer`.
- `presign` and object metadata are backend capabilities — the local filesystem raises
  `UnsupportedOperationError`; check `buckets action=info` capabilities first.
- `metadata_set` **replaces** user metadata, it does not merge.

## Related
- **Buckets & stores:** `objectstore-bucket-administration`.
- **Bulk / disk transfer:** `objectstore-data-transfer`.
- **KG ingestion:** the `objectstore_ingest` tool mirrors bucket/object *metadata*
  into the epistemic-graph as `:Bucket`/`:Object` nodes — it never copies object bytes.
