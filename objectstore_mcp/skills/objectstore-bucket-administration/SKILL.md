---
name: objectstore-bucket-administration
skill_type: skill
description: >-
  Bucket administration through the objectstore-mcp MCP server: list stores and buckets, create, inspect and (gated) delete buckets, and manage bucket lifecycle rules and versioning on S3-compatible stores. Use when the agent must provision or audit buckets, discover which stores the caller may reach, set retention or expiry, or turn versioning on. Do NOT use for object reads and writes (objectstore-object-operations) or local file transfers (objectstore-data-transfer).
license: MIT
tags: [objectstore, s3, buckets, lifecycle, versioning, mcp]
metadata:
  author: Knuckles-Team
  version: '0.2.0'
---
# ObjectStore Bucket Administration

## When to use
- Discover the stores your identity may reach, and the buckets in a store.
- Create a bucket, check it exists, inspect it, or delete an empty one (when enabled).
- Set lifecycle rules: expire objects under a prefix, expire noncurrent versions, abort
  stale multipart uploads, or transition to another storage class.
- Read or change a bucket's versioning state.

## Tools
| Operation | Tool | Key parameters |
|-----------|------|----------------|
| Stores | `objectstore_list_stores` | none |
| Buckets | `objectstore_list_buckets` | none |
| Create | `objectstore_create_bucket` | `bucket`, `location` |
| Exists / inspect | `objectstore_bucket_exists` / `objectstore_bucket_info` | `bucket` |
| Backend capabilities | `objectstore_capabilities` | none |
| Delete empty bucket | `objectstore_delete_bucket` | `bucket`, `confirm` (needs `OBJECTSTORE_ALLOW_BUCKET_DELETE=true`) |
| Lifecycle read | `objectstore_get_bucket_lifecycle` | `bucket`, `store` |
| Lifecycle replace | `objectstore_put_bucket_lifecycle` | `bucket`, `rules` [{`id`, `prefix`, `enabled`, `expiration_days`, `noncurrent_expiration_days`, `abort_incomplete_multipart_days`, `transition_days`, `storage_class`}] |
| Lifecycle clear | `objectstore_delete_bucket_lifecycle` | `bucket`, `store` |
| Versioning | `objectstore_get_bucket_versioning` / `objectstore_put_bucket_versioning` | `bucket`, `status` Enabled/Suspended |

Lifecycle and versioning work on `s3` stores only; other backends refuse with
`STORAGE_UNSUPPORTED`.

## Workflow
1. `objectstore_list_stores`, then `objectstore_list_buckets`.
2. Create or inspect the bucket.
3. Read the current lifecycle before replacing it: `objectstore_put_bucket_lifecycle`
   replaces the whole rule set. Every rule needs at least one action.
4. Read it back with `objectstore_get_bucket_lifecycle` and report the rule ids.

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
