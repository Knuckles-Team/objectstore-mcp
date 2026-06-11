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
{"tool": "buckets", "arguments": {"action": "stores"}}
```

## Tool reference

### `objects`

| Action | Required params | Optional params |
|---|---|---|
| `list` | — | `bucket`, `prefix`, `delimiter`, `max_keys`, `token` |
| `head` | `key` | `bucket` |
| `get` | `key` | `bucket`, `mode` (`auto`/`text`/`base64`), `max_bytes` |
| `put` | `key`, `text` or `content_base64` | `bucket`, `content_type`, `metadata` |
| `copy` | `key`, `dest_key` | `bucket`, `dest_bucket` |
| `move` | `key`, `dest_key` | `bucket`, `dest_bucket` |
| `delete` | `bucket`, `key` (both explicit) | — |
| `delete_batch` | `bucket`, `prefix` (both explicit) | `max_keys`, `dry_run` (default `true`) |
| `presign` | `key` | `bucket`, `method` (`GET`/`PUT`), `expires_in` |
| `metadata_get` | `key` | `bucket` |
| `metadata_set` | `key`, `metadata` | `bucket` |

`get` returns `{"encoding": "text"|"base64", "content": ...}`; `auto` mode
falls back to base64 for non-UTF-8 payloads.

### `buckets`

| Action | Required params | Notes |
|---|---|---|
| `list` | — | |
| `create` | `bucket` (or store default) | optional `location` |
| `delete` | `bucket` (explicit) | empty buckets only; needs `OBJECTSTORE_ALLOW_BUCKET_DELETE=true` |
| `exists` | `bucket` | |
| `info` | `bucket` | includes the backend's capability flags |
| `stores` | — | configured named stores |

### `transfer`

| Action | Required params | Optional params |
|---|---|---|
| `upload` | `local_path` | `bucket`, `key` (default: file name), `content_type`, `metadata` |
| `download` | `key`, `local_path` | `bucket`, `overwrite` (default `false`) |
| `upload_dir` | `local_dir` | `bucket`, `prefix`, `max_keys` |
| `download_prefix` | `local_dir` | `bucket`, `prefix`, `max_keys`, `overwrite` |

## Safety model

- **Size caps** — `get`/`put` and transfers are capped
  (`OBJECTSTORE_MAX_GET_BYTES`, `OBJECTSTORE_MAX_PUT_BYTES`,
  `OBJECTSTORE_MAX_TRANSFER_BYTES`); callers can lower but never exceed them.
- **Key caps** — listing pages clamp to `OBJECTSTORE_MAX_LIST_KEYS`; batch
  operations clamp to `OBJECTSTORE_MAX_BATCH_KEYS`.
- **Deletes are explicit** — `delete` requires both `bucket` and `key` in
  params (store default buckets do not apply) and rejects wildcard
  characters. `delete_batch` requires an explicit bucket and a non-empty
  prefix, is capped, and **previews (dry-run) by default** — pass
  `"dry_run": false` to execute.
- **Flags** — object deletes are governed by `OBJECTSTORE_ALLOW_DELETE`
  (default on); bucket deletes by `OBJECTSTORE_ALLOW_BUCKET_DELETE`
  (default off) and only ever remove empty buckets.
