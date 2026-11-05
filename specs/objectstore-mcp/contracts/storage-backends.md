# Storage backends seam contract

Provider: scion-sdk SCION-CENTRALIZED-CAPABILITIES-R042
Consumer: objectstore-mcp CONN-OBJECTSTORE-MCP-R001

Provider spec: [SCION-CENTRALIZED-CAPABILITIES](https://github.com/Knuckles-Team/scion-sdk/blob/main/specs/centralized-capabilities/requirements.md).

## Wire shape

The seam is a Python import. The connector imports `ObjectStoreBackend`, the value types, `StorageError` and `create_backend` from `scion_sdk.storage`. It builds each `StoreConfig` with `parse_stores` from `OBJECTSTORE_STORES`. Each store holds secret references in its `credentials` map:

```json
{"media": {"backend": "s3", "endpoint": "https://objects.example", "bucket": "media",
           "credentials": {"access_key_id": "env://MEDIA_KEY", "secret_access_key": "openbao://kv/media#secret"}},
 "share": {"backend": "webdav", "endpoint": "https://files.example/dav/files/svc",
           "credentials": {"username": "env://SHARE_USER", "password": "openbao://kv/share#password"}}}
```

## Refusal codes

`STORAGE_NOT_FOUND`, `STORAGE_EXISTS`, `STORAGE_BUCKET_NOT_EMPTY`, `STORAGE_UNSUPPORTED`, `STORAGE_NAME_INVALID`, `STORAGE_DEPENDENCY_MISSING`, `STORAGE_TOO_LARGE`, `STORAGE_BACKEND_FAILED`, `STORAGE_SECRET_LITERAL`, `STORAGE_CONFIG_INVALID`, `STORAGE_EGRESS_REFUSED`. The connector maps each code to its tool error and adds no storage code of its own.

## Authoritative types

- `scion_sdk/storage/base.py`, `scion_sdk/storage/config.py` and `scion_sdk/storage/factory.py` in scion-sdk.

## Test vectors

- `tests/storage/` in scion-sdk.
- `tests/test_sdk_backends.py` in this repository.
