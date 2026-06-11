"""get_client(): golden auth entry point wraps failures in AUTHENTICATION ERROR."""

import pytest

from objectstore_mcp.auth import get_client, reset_backend_cache


def test_get_client_unknown_store_raises_authentication_error():
    reset_backend_cache()
    with pytest.raises(RuntimeError) as exc_info:
        get_client("definitely-not-a-store")
    assert "AUTHENTICATION ERROR" in str(exc_info.value)


def test_get_client_resolves_local_store(monkeypatch, tmp_path):
    monkeypatch.setenv("OBJECTSTORE_FS_ROOT", str(tmp_path))
    monkeypatch.delenv("OBJECTSTORE_STORES", raising=False)
    monkeypatch.delenv("OBJECTSTORE_DEFAULT_STORE", raising=False)
    reset_backend_cache()
    backend = get_client("local")
    assert backend is not None
    reset_backend_cache()
