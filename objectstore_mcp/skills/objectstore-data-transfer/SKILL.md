---
name: objectstore-data-transfer
skill_type: skill
description: >-
  Move files between the server's local filesystem and object storage through the objectstore-mcp MCP server: upload or download one file, upload a directory under a prefix, or download every object under a prefix, all size- and count-capped. Use for staging, backups and restores that run on the server host. Not for in-memory object I/O or bucket settings.
license: MIT
tags: [objectstore, s3, transfer, backup, mcp]
metadata:
  author: Knuckles-Team
  version: '0.2.0'
---
# ObjectStore Data Transfer

Scope: Move files between the server's local filesystem and object storage through the objectstore-mcp MCP server: upload or download one file, upload a directory under a prefix, or download every object under a prefix, all size- and count-capped. Use for staging, backups and restores that run on the server host. Do NOT use for in-memory object reads and writes (objectstore-object-operations) or bucket settings (objectstore-bucket-administration).

## When to use
- Upload a file the server can read to a bucket, or download an object to a server path.
- Upload a whole directory under a key prefix, or restore a prefix into a directory.

Paths are on the machine that runs the server, not the caller's machine. To hand a file
to another system, use a presigned URL instead (objectstore-object-operations).

## Steps

1. Confirm the destination bucket with `objectstore_bucket_exists`.
   Verify it returns true, and create it through objectstore-bucket-administration if not.
2. Transfer one file with `objectstore_upload_file` or `objectstore_download_file` (`bucket`, `key`, `local_path`).
   Verify the call reports the bytes moved.
3. Transfer a tree with `objectstore_upload_directory` or `objectstore_download_prefix`, setting `max_keys` explicitly.
   Verify the reported object count is at or below that cap.
4. Check the result with `objectstore_list_objects` under the prefix.
   Verify the keys and sizes match the source and report them.

## Failure recovery

| Failure | Cause | Recovery |
|---------|-------|----------|
| Refused before any byte moves | The file exceeds `OBJECTSTORE_MAX_TRANSFER_BYTES` or the directory exceeds the batch cap | Split the transfer into smaller files or prefixes, or lower `max_keys`, and run it again |
| `local_path` not found or download skipped | The path is on the server host, not the caller, or the target exists and `overwrite` is unset | Use a path that exists on the server host, and pass `overwrite=true` only when replacing is intended |
| `STORAGE_EGRESS_REFUSED` | The endpoint is not in `allowed_private_hosts` | Report the code, and ask the operator to add the endpoint to the store configuration |

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

## Refusals
A store failure names its code: `STORAGE_NOT_FOUND`, `STORAGE_EXISTS`,
`STORAGE_BUCKET_NOT_EMPTY`, `STORAGE_UNSUPPORTED` (for example presign or lifecycle on a
filesystem store), `STORAGE_EGRESS_REFUSED` (endpoint not in `allowed_private_hosts`),
`STORAGE_DEPENDENCY_MISSING`, or `not entitled` (the identity lacks the store role).
Report the code; do not retry a refusal unchanged.
