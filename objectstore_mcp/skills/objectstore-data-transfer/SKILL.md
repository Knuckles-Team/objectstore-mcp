---
name: objectstore-data-transfer
skill_type: skill
description: >-
  Bulk data transfer between the local filesystem and object storage via the
  objectstore-mcp MCP server — upload/download single files and whole
  directories/prefixes with the action-routed `transfer` tool, across S3/MinIO/R2,
  GCS, Azure Blob, and a local filesystem store. Use when the agent must move a file
  or a tree of files to/from a bucket (backups, staging, restores) under enforced size
  and key-count caps. Do NOT use for in-memory object reads/writes (use
  objectstore-object-operations) or bucket lifecycle (use
  objectstore-bucket-administration).
license: MIT
tags: [objectstore, transfer, upload, download, backup, mcp]
metadata:
  author: Genius
  version: '0.1.0'
---
# ObjectStore Data Transfer

Move bytes between local disk and object storage without holding them in the
conversation. Every transfer is size-capped, and directory/prefix transfers are also
key-count capped.

## When to use
- Upload a single local file to an object (`upload`).
- Download a single object to a local path (`download`).
- Upload a local directory tree under a key prefix (`upload_dir`).
- Download all objects under a prefix into a local directory (`download_prefix`).

## When NOT to use
- Read/write an object's bytes in-band (text/base64), tag, copy, or delete →
  `objectstore-object-operations`.
- Create/delete/inspect buckets or list stores → `objectstore-bucket-administration`.
- Transfers exceeding the caps — narrow the prefix/dir or raise the env caps; do not
  loop tiny transfers to evade them.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`objectstore-mcp`** MCP server. The
local paths are on the **server's** filesystem, not the agent's.

| Variable | Required | Notes |
|----------|----------|-------|
| `OBJECTSTORE_STORES` | optional | JSON map of named stores → backend + settings |
| `OBJECTSTORE_DEFAULT_STORE` | optional | Store used when `store` is omitted |
| `OBJECTSTORE_MAX_TRANSFER_BYTES` | optional | Per-transfer byte cap (default 100 MiB) |
| `OBJECTSTORE_MAX_BATCH_KEYS` | optional | Max files/objects per dir/prefix transfer |
| S3 `AWS_*`/profile · GCS `GOOGLE_APPLICATION_CREDENTIALS` · Azure `AZURE_STORAGE_CONNECTION_STRING` | per-backend | Provider SDK credential chains |

## Tools & actions
| Tool | Actions |
|------|---------|
| `transfer` | `upload`, `download`, `upload_dir`, `download_prefix` |

Each call takes `action`, a `params_json` **JSON string**, and optional `store`.

### Key parameters
- `upload` — `bucket`, `local_path`, optional `key` (defaults to the filename),
  `content_type`, `metadata`.
- `download` — `bucket`, `key`, `local_path`, optional `overwrite` (default false).
- `upload_dir` — `bucket`, `local_dir`, optional `prefix`, `max_keys`.
- `download_prefix` — `bucket`, `prefix`, `local_dir`, optional `max_keys`, `overwrite`.

## Recipes (`params_json`)
Upload one file, naming the key:
```json
{"bucket":"backups","local_path":"/data/db.dump","key":"nightly/db.dump","content_type":"application/octet-stream"}
```
Download an object (refusing to clobber):
```json
{"bucket":"backups","key":"nightly/db.dump","local_path":"/restore/db.dump","overwrite":false}
```
Upload a directory tree under a prefix:
```json
{"bucket":"backups","local_dir":"/data/site","prefix":"site/","max_keys":50}
```
Download a whole prefix:
```json
{"bucket":"backups","prefix":"site/","local_dir":"/restore/site","max_keys":50,"overwrite":true}
```

## Gotchas
- `params_json` is a **string** of JSON, not an object.
- Paths are on the **server**, not the agent host — the file/dir must exist there.
- `download`/`download_prefix` refuse to overwrite unless `overwrite:true`.
- `upload_dir`/`download_prefix` fail fast if the tree exceeds `max_keys` (bounded by
  `OBJECTSTORE_MAX_BATCH_KEYS`) or the total exceeds `OBJECTSTORE_MAX_TRANSFER_BYTES` —
  narrow the scope rather than raising caps blindly.
- `upload_dir` keys are `prefix` + the file's POSIX path relative to `local_dir`.

## Related
- **Object CRUD / presign / metadata:** `objectstore-object-operations`.
- **Bucket lifecycle & store discovery:** `objectstore-bucket-administration`.
- **KG ingestion:** the `objectstore_ingest` tool records the resulting object
  *metadata* (`:Object` nodes) — object bytes are never copied into the graph.
