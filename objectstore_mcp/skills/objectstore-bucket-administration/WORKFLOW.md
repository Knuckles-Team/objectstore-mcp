# Objectstore Bucket Administration

Bucket/container administration and store inspection over the objectstore-mcp MCP server — list, create, check existence, inspect, and (gated) delete buckets, and enumerate the configured named stores and their backend capabilities via the action-routed `buckets` tool. Use when the agent must provision or audit buckets, discover which stores/backends are wired up, or check whether presigned URLs and object metadata are supported. Do NOT use for object-level read/write (use objectstore-object-operations) or file/directory transfer (use objectstore-data-transfer).

# ObjectStore Bucket Administration

Provision and audit buckets/containers and inspect the configured stores behind the
objectstore-mcp server. Bucket deletes are deliberately conservative: empty-only and
off by default.

## When to use
- List, create, or check existence of a bucket/container.
- Inspect one bucket (`info`) — location/details plus the backend's capabilities.
- Enumerate the configured named stores (`stores`) and their backend + default bucket.
- Delete an **empty** bucket, when explicitly enabled.

## When NOT to use
- Read/write/list/delete objects → `objectstore-object-operations`.
- Move files or directories to/from local disk → `objectstore-data-transfer`.
- Emptying a non-empty bucket — `delete` refuses non-empty buckets; clear objects first
  with `objects action=delete_batch`.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`objectstore-mcp`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `OBJECTSTORE_STORES` | optional | JSON map of named stores → backend + settings |
| `OBJECTSTORE_DEFAULT_STORE` | optional | Store used when `store` is omitted |
| `OBJECTSTORE_ALLOW_BUCKET_DELETE` | optional | Master switch for bucket deletes (**default false**) |
| S3 `AWS_*`/profile · GCS `GOOGLE_APPLICATION_CREDENTIALS` · Azure `AZURE_STORAGE_CONNECTION_STRING` | per-backend | Provider SDK credential chains |

## Tools & actions
| Tool | Actions |
|------|---------|
| `buckets` | `list`, `create`, `delete`, `exists`, `info`, `stores` |

Each call takes `action`, a `params_json` **JSON string**, and optional `store`.
`stores` takes no store and needs no params.

### Key parameters
- `bucket` — the target bucket for `create`/`delete`/`exists`/`info`.
- `create` — optional `location` (region/location constraint, where the backend honors it).

## Recipes (`params_json`)
Enumerate configured stores (no params):
```json
{}
```
Create a bucket in a region:
```json
{"bucket":"acme-reports","location":"us-east-1"}
```
Check existence:
```json
{"bucket":"acme-reports"}
```
Inspect a bucket + its backend capabilities (`info`):
```json
{"bucket":"acme-reports"}
```

## Gotchas
- `params_json` is a **string** of JSON, not an object.
- Bucket delete is **off by default** — set `OBJECTSTORE_ALLOW_BUCKET_DELETE=true`, and
  it still refuses non-empty buckets (`BucketNotEmptyError`).
- `stores` is the discovery entry point — call it first to learn valid `store` names and
  each store's default bucket/backend before other actions.
- `info` returns a `capabilities` map (`presigned_urls`, `object_metadata`,
  `bucket_location`); check it before relying on presign/metadata in
  `objectstore-object-operations`.
- The `local` filesystem store always exists even with no `OBJECTSTORE_STORES` set.

## Related
- **Object CRUD:** `objectstore-object-operations`.
- **File/dir transfer:** `objectstore-data-transfer`.
- **KG ingestion:** the `objectstore_ingest` tool (`action=buckets`) mirrors the store's
  buckets into the epistemic-graph as `:Bucket` nodes under their `:ObjectStore`.
