"""Shared fixtures: isolated filesystem stores and clean env/caches."""

import pytest

from objectstore_mcp.auth import reset_backend_cache
from objectstore_mcp.api.api_client_filesystem import FilesystemBackend

ENV_VARS = [
    "OBJECTSTORE_STORES",
    "OBJECTSTORE_DEFAULT_STORE",
    "OBJECTSTORE_FS_ROOT",
    "OBJECTSTORE_MAX_GET_BYTES",
    "OBJECTSTORE_MAX_PUT_BYTES",
    "OBJECTSTORE_MAX_TRANSFER_BYTES",
    "OBJECTSTORE_MAX_BATCH_KEYS",
    "OBJECTSTORE_MAX_LIST_KEYS",
    "OBJECTSTORE_ALLOW_DELETE",
    "OBJECTSTORE_ALLOW_BUCKET_DELETE",
]


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    """Each test starts with no objectstore env vars and an empty cache."""
    for var in ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    reset_backend_cache()
    yield
    reset_backend_cache()


@pytest.fixture
def fs_backend(tmp_path):
    """A filesystem backend rooted at a per-test temp directory."""
    return FilesystemBackend(root=str(tmp_path / "store"))


@pytest.fixture
def local_store_env(tmp_path, monkeypatch):
    """Point the implicit 'local' store at a per-test temp root."""
    root = tmp_path / "local-store"
    monkeypatch.setenv("OBJECTSTORE_FS_ROOT", str(root))
    return root
