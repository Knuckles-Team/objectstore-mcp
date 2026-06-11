"""API client facade: re-exports and factory behavior (golden test_api_wrapper)."""

from objectstore_mcp.api_client import (
    BACKEND_ALIASES,
    ObjectStoreBackend,
    ObjectStoreError,
    create_backend,
)
from objectstore_mcp.config import StoreConfig


def test_facade_reexports_protocol_and_factory():
    assert isinstance(BACKEND_ALIASES, dict)
    assert callable(create_backend)
    assert ObjectStoreBackend is not None


def test_create_backend_via_facade(tmp_path):
    store = StoreConfig(name="t", backend="filesystem", root=str(tmp_path))
    backend = create_backend(store)
    backend.create_bucket("b")
    backend.put_object("b", "k.txt", b"hello", content_type="text/plain")
    data = backend.get_object("b", "k.txt")
    assert data == b"hello"


def test_create_backend_unknown_raises():
    store = StoreConfig(name="t", backend="carrier-pigeon")
    try:
        create_backend(store)
        raise AssertionError("expected ObjectStoreError")
    except ObjectStoreError as exc:
        assert "carrier-pigeon" in str(exc)
