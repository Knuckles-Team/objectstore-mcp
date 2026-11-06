# Usage

## Running the server

```bash
objectstore-mcp                                                    # stdio
objectstore-mcp --transport streamable-http --host 0.0.0.0 --port 8000
python -m objectstore_mcp                                          # module form
```

A `/health` route answers `{"status": "OK"}` on HTTP transports.

## Stores

Tools take an optional `store` argument naming an entry from
`OBJECTSTORE_STORES`. When omitted, `OBJECTSTORE_DEFAULT_STORE` applies
(default: the first configured store, else the built-in `local` filesystem
store). A store may carry a default `bucket`, so most calls only need a key.

Inspect the registry at runtime:

```jsonc
{"tool": "objectstore_list_stores", "arguments": {}}
```

## Tool reference

One typed tool per operation. The per-operation tools of the backend protocol
(`objectstore_list_buckets`, `objectstore_put_object`, ...) act on the default
store; every other tool takes an optional `store`.

| MCP Tool | Parameters | Description |
|----------|------------|-------------|
| `objectstore_bucket_exists` | `bucket` | Return True when the bucket exists. |
| `objectstore_bucket_info` | `bucket` | Describe one bucket. Raises NotFoundError when absent. |
| `objectstore_capabilities` | — | Advertise optional capabilities. |
| `objectstore_copy_object` | `dst_bucket`, `dst_key`, `src_bucket`, `src_key` | Server-side (where possible) copy of one object. |
| `objectstore_create_bucket` | `bucket`, `location` | Create a bucket. Raises AlreadyExistsError if it exists. |
| `objectstore_delete_bucket` | `bucket`, `confirm` | Delete an EMPTY bucket. Raises BucketNotEmptyError otherwise. |
| `objectstore_delete_bucket_lifecycle` | `bucket`, `store` | Remove every lifecycle rule from a bucket. |
| `objectstore_delete_object` | `bucket`, `confirm`, `key` | Delete exactly one object. Raises NotFoundError when absent. |
| `objectstore_delete_object_tags` | `bucket`, `key`, `store` | Remove every tag from an object. |
| `objectstore_delete_objects_by_prefix` | `bucket`, `dry_run`, `max_keys`, `prefix`, `store` | Delete objects under a non-empty prefix (dry run by default, count-capped). |
| `objectstore_download_file` | `bucket`, `key`, `local_path`, `overwrite`, `store` | Download one object to a local file (capped by OBJECTSTORE_MAX_TRANSFER_BYTES). |
| `objectstore_download_prefix` | `bucket`, `local_dir`, `max_keys`, `overwrite`, `prefix`, `store` | Download the objects under a prefix into a local directory (capped). |
| `objectstore_get_bucket_lifecycle` | `bucket`, `store` | Read a bucket's lifecycle rules (empty list when none are set). |
| `objectstore_get_bucket_versioning` | `bucket`, `store` | Read a bucket's versioning state (Enabled, Suspended or unset). |
| `objectstore_get_object` | `bucket`, `key`, `max_bytes` | Download an object's bytes. Raises TooLargeError when the |
| `objectstore_get_object_metadata` | `bucket`, `key` | Return the user metadata of one object. |
| `objectstore_get_object_tags` | `bucket`, `key`, `store` | Read an object's tag set. |
| `objectstore_head_object` | `bucket`, `key` | Stat one object without downloading it. |
| `objectstore_ingest_buckets` | `store` | Mirror the store's buckets into the knowledge graph as :Bucket nodes. |
| `objectstore_ingest_objects` | `bucket`, `max_keys`, `prefix`, `store` | Mirror object metadata under a prefix into the knowledge graph as :Object nodes. |
| `objectstore_list_buckets` | — | List all buckets/containers visible to the credentials. |
| `objectstore_list_objects` | `bucket`, `continuation_token`, `delimiter`, `max_keys`, `prefix` | List objects under ``prefix``, optionally folding at ``delimiter``. |
| `objectstore_list_stores` | — | List the named stores the caller is entitled to, with backend and endpoint. |
| `objectstore_move_object` | `dst_bucket`, `dst_key`, `src_bucket`, `src_key`, `store` | Move one object: copy it to dst_bucket/dst_key, then delete the source. |
| `objectstore_presigned_url` | `bucket`, `expires_in`, `key`, `method` | Mint a presigned URL. Raises UnsupportedOperationError when the |
| `objectstore_put_bucket_lifecycle` | `bucket`, `rules`, `store` | Replace a bucket's lifecycle rules (expiry, noncurrent expiry, transitions). |
| `objectstore_put_bucket_versioning` | `bucket`, `status`, `store` | Enable or suspend object versioning on a bucket. |
| `objectstore_put_object` | `bucket`, `content_type`, `data`, `key`, `metadata` | Upload bytes to ``bucket/key`` (overwrites). |
| `objectstore_put_object_tags` | `bucket`, `key`, `store`, `tags` | Replace an object's tag set (at most 10 tags). |
| `objectstore_set_object_metadata` | `bucket`, `key`, `metadata` | Replace the user metadata of one object. |
| `objectstore_upload_directory` | `bucket`, `local_dir`, `max_keys`, `prefix`, `store` | Upload every file under a local directory to objects under a prefix (capped). |
| `objectstore_upload_file` | `bucket`, `content_type`, `key`, `local_path`, `metadata`, `store` | Upload one local file to an object (capped by OBJECTSTORE_MAX_TRANSFER_BYTES). |

Lifecycle, versioning and tag tools work on `s3` stores; other backends refuse
with `STORAGE_UNSUPPORTED`.

## Safety model

- **Size caps** — `get`/`put` and transfers are capped
  (`OBJECTSTORE_MAX_GET_BYTES`, `OBJECTSTORE_MAX_PUT_BYTES`,
  `OBJECTSTORE_MAX_TRANSFER_BYTES`); callers can lower but never exceed them.
- **Key caps** — listing pages clamp to `OBJECTSTORE_MAX_LIST_KEYS`; batch
  operations clamp to `OBJECTSTORE_MAX_BATCH_KEYS`.
- **Removes are explicit** — `objectstore_delete_object` requires both `bucket` and `key` and rejects wildcard
  characters. `objectstore_delete_objects_by_prefix` requires an explicit bucket and a non-empty
  prefix, is capped, and **previews (dry-run) by default** — pass
  `"dry_run": false` to ran.
- **Flags** — object removes are governed by `OBJECTSTORE_ALLOW_DELETE`
  (default on); bucket removes by `OBJECTSTORE_ALLOW_BUCKET_DELETE`
  (default off) and only ever remove empty buckets.
