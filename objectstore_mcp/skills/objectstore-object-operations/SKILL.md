---
name: objectstore-object-operations
skill_type: skill
description: >-
  Object-level operations through the objectstore-mcp MCP server with one typed tool per operation: list, head, get, put, copy, move, delete (single or by prefix with a dry run), presigned URLs, user metadata and object tags. Use when the agent must read or write an object, page a bucket by prefix, mint a presigned URL, tag an object, or delete objects. Do NOT use for bucket provisioning, lifecycle or versioning (objectstore-bucket-administration) or moving local files (objectstore-data-transfer).
license: MIT
tags: [objectstore, s3, objects, presign, tags, mcp]
metadata:
  author: Knuckles-Team
  version: '0.2.0'
---
# ObjectStore Object Operations

## When to use
- List objects under a prefix (`delimiter="/"` folds folders), with `continuation_token` paging.
- Stat, read (size-capped) or write a small object; copy or move it.
- Mint a presigned GET or PUT URL for a handoff to another system.
- Read or replace an object's user metadata or its tag set.
- Delete one object, or every object under a prefix after a dry run.

## Tools
| Operation | Tool | Key parameters |
|-----------|------|----------------|
| List | `objectstore_list_objects` | `bucket`, `prefix`, `delimiter`, `max_keys`, `continuation_token` |
| Stat | `objectstore_head_object` | `bucket`, `key` |
| Read | `objectstore_get_object` | `bucket`, `key`, `max_bytes` (clamped to the cap) |
| Write | `objectstore_put_object` | `bucket`, `key`, `data`, `content_type`, `metadata` |
| Copy | `objectstore_copy_object` | `src_bucket`, `src_key`, `dst_bucket`, `dst_key` |
| Move | `objectstore_move_object` | as copy, plus optional `store` |
| Delete one | `objectstore_delete_object` | `bucket`, `key`, `confirm` (no wildcards) |
| Delete by prefix | `objectstore_delete_objects_by_prefix` | `bucket`, `prefix`, `dry_run` (default true), `max_keys` |
| Presigned URL | `objectstore_presigned_url` | `bucket`, `key`, `method` GET/PUT, `expires_in` seconds |
| Metadata | `objectstore_get_object_metadata` / `objectstore_set_object_metadata` | `bucket`, `key`, `metadata` |
| Tags | `objectstore_get_object_tags` / `objectstore_put_object_tags` / `objectstore_delete_object_tags` | `bucket`, `key`, `tags` (at most 10) |

The per-operation tools act on the default store; the composite and tag tools take an
optional `store`.

## Workflow
1. `objectstore_list_objects` or `objectstore_head_object` to confirm the object exists.
2. Make the change. For a prefix delete, run `objectstore_delete_objects_by_prefix`
   with `dry_run=true`, show the matched keys, then rerun with `dry_run=false`.
3. Verify with `objectstore_head_object` or `objectstore_get_object_tags`.
4. Report each key changed with its etag.

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
