"""Store-registry and limits configuration tests (CONCEPT:OBJ-1.1)."""

import json

import pytest

from objectstore_mcp.auth import get_backend, resolve_store
from objectstore_mcp.backends import BACKEND_ALIASES, create_backend
from objectstore_mcp.backends.base import ObjectStoreError
from objectstore_mcp.backends.filesystem import FilesystemBackend
from objectstore_mcp.config import (
    LOCAL_STORE_NAME,
    StoreConfig,
    default_store_name,
    load_limits,
    load_stores,
)


def test_local_store_always_present():
    stores = load_stores()
    assert LOCAL_STORE_NAME in stores
    assert stores[LOCAL_STORE_NAME].backend == "filesystem"


def test_stores_json_parsed(monkeypatch):
    monkeypatch.setenv(
        "OBJECTSTORE_STORES",
        json.dumps(
            {
                "media": {"backend": "s3", "bucket": "media-prod", "profile": "prod"},
                "minio": {
                    "backend": "s3",
                    "endpoint": "http://minio.arpa:9000",
                    "custom_flag": True,
                },
            }
        ),
    )
    stores = load_stores()
    assert stores["media"].bucket == "media-prod"
    assert stores["media"].profile == "prod"
    assert stores["minio"].endpoint == "http://minio.arpa:9000"
    assert stores["minio"].options == {"custom_flag": True}
    assert LOCAL_STORE_NAME in stores


def test_invalid_stores_json_rejected(monkeypatch):
    monkeypatch.setenv("OBJECTSTORE_STORES", "{not json")
    with pytest.raises(ValueError, match="not valid JSON"):
        load_stores()
    monkeypatch.setenv("OBJECTSTORE_STORES", '["a"]')
    with pytest.raises(ValueError, match="JSON object"):
        load_stores()
    monkeypatch.setenv("OBJECTSTORE_STORES", '{"x": {"bucket": "b"}}')
    with pytest.raises(ValueError, match="backend"):
        load_stores()


def test_default_store_resolution(monkeypatch):
    assert default_store_name(load_stores()) == LOCAL_STORE_NAME
    monkeypatch.setenv(
        "OBJECTSTORE_STORES", '{"media": {"backend": "s3", "bucket": "b"}}'
    )
    assert default_store_name(load_stores()) == "media"
    monkeypatch.setenv("OBJECTSTORE_DEFAULT_STORE", "local")
    assert default_store_name(load_stores()) == "local"
    monkeypatch.setenv("OBJECTSTORE_DEFAULT_STORE", "ghost")
    with pytest.raises(ValueError, match="ghost"):
        default_store_name(load_stores())


def test_resolve_unknown_store():
    with pytest.raises(ObjectStoreError, match="Unknown store"):
        resolve_store("ghost")


def test_get_backend_caches(local_store_env):
    first, config = get_backend("local")
    second, _ = get_backend("local")
    assert first is second
    assert isinstance(first, FilesystemBackend)
    assert config.name == "local"


def test_limits_defaults_and_overrides(monkeypatch):
    limits = load_limits()
    assert limits.max_get_bytes == 10 * 1024 * 1024
    assert limits.max_transfer_bytes == 100 * 1024 * 1024
    assert limits.max_batch_keys == 100
    assert limits.allow_object_delete is True
    assert limits.allow_bucket_delete is False

    monkeypatch.setenv("OBJECTSTORE_MAX_GET_BYTES", "1024")
    monkeypatch.setenv("OBJECTSTORE_ALLOW_DELETE", "false")
    monkeypatch.setenv("OBJECTSTORE_ALLOW_BUCKET_DELETE", "true")
    limits = load_limits()
    assert limits.max_get_bytes == 1024
    assert limits.allow_object_delete is False
    assert limits.allow_bucket_delete is True

    monkeypatch.setenv("OBJECTSTORE_MAX_GET_BYTES", "not-a-number")
    with pytest.raises(ValueError, match="integer"):
        load_limits()


def test_backend_aliases_resolve(tmp_path):
    for alias in ["filesystem", "fs", "local"]:
        backend = create_backend(
            StoreConfig(name="x", backend=alias, root=str(tmp_path / alias))
        )
        assert isinstance(backend, FilesystemBackend)
    assert BACKEND_ALIASES["minio"] == "s3"
    assert BACKEND_ALIASES["r2"] == "s3"
    assert BACKEND_ALIASES["gcp"] == "gcs"
    assert BACKEND_ALIASES["azure_blob"] == "azure"


def test_unknown_backend_rejected():
    with pytest.raises(ObjectStoreError, match="Unknown backend"):
        create_backend(StoreConfig(name="x", backend="carrier-pigeon"))
