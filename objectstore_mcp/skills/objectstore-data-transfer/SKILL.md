---
name: objectstore-data-transfer
skill_type: skill
description: >-
  Move files between the server's local filesystem and object storage through the objectstore-mcp MCP server: upload or download one file, upload a directory under a prefix, or download every object under a prefix, all size- and count-capped. Use for staging, backups and restores that run on the server host. Do NOT use for in-memory object reads and writes (objectstore-object-operations) or bucket settings (objectstore-bucket-administration).
license: MIT
tags: [objectstore, s3, transfer, backup, mcp]
metadata:
  author: Knuckles-Team
  version: '0.2.0'
---
# ObjectStore Data Transfer

## When to use
- Upload a file the server can read to a bucket, or download an object to a server path.
- Upload a whole directory under a key prefix, or restore a prefix into a directory.

Paths are on the machine that runs the server, not the caller's machine. To hand a file
to another system, use a presigned URL instead (objectstore-object-operations).

## Tools
| Operation | Tool | Key parameters |
|-----------|------|----------------|
| Upload file | `objectstore_upload_file` | `bucket`, `local_path`, `key`, `content_type`, `metadata`, `store` |
| Download file | `objectstore_download_file` | `bucket`, `key`, `local_path`, `overwrite`, `store` |
| Upload directory | `objectstore_upload_directory` | `bucket`, `local_dir`, `prefix`, `max_keys`, `store` |
| Download prefix | `objectstore_download_prefix` | `bucket`, `prefix`, `local_dir`, `max_keys`, `overwrite`, `store` |

## Workflow
1. Confirm the bucket exists (`objectstore_bucket_exists`).
2. Transfer. A file over `OBJECTSTORE_MAX_TRANSFER_BYTES`, or a directory over the batch
   cap, is refused before any byte moves.
3. Verify with `objectstore_list_objects` and report the keys and sizes.

## Prerequisites & environment
Connect to the **`objectstore-mcp`** MCP server (directly, or through the fleet gateway).
Stores come from `OBJECTSTORE_STORES` (JSON); a zero-infra `local` filesystem store
always exists. Store credentials are secret references in each store's `credentials`
map; the server never reads an ambient provider chain. The caller's identity must hold
`objectstore:<store>` or `objectstore:admin` to reach a store.

| Variable | Notes |
|----------|-------|
| `OBJECTSTORE_STORES` | JSON map of named stores: backend, endpoint, `allowed_private_hosts`, `credentials` refs |
| `OBJECTSTORE_DEFAULT_STORE` | Store used when `store` is omitted (the per-operation tools always use it) |
| `OBJECTSTORE_MAX_GET_BYTES` / `OBJECTSTORE_MAX_PUT_BYTES` / `OBJECTSTORE_MAX_TRANSFER_BYTES` | Size caps |
| `OBJECTSTORE_MAX_LIST_KEYS` / `OBJECTSTORE_MAX_BATCH_KEYS` | List and batch caps |
| `OBJECTSTORE_ALLOW_DELETE` / `OBJECTSTORE_ALLOW_BUCKET_DELETE` | Delete switches (bucket deletes default off) |

## Refusals
A store failure names its code: `STORAGE_NOT_FOUND`, `STORAGE_EXISTS`,
`STORAGE_BUCKET_NOT_EMPTY`, `STORAGE_UNSUPPORTED` (for example presign or lifecycle on a
filesystem store), `STORAGE_EGRESS_REFUSED` (endpoint not in `allowed_private_hosts`),
`STORAGE_DEPENDENCY_MISSING`, or `not entitled` (the identity lacks the store role).
Report the code; do not retry a refusal unchanged.
