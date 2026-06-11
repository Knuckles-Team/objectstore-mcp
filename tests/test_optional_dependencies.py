"""Optional-dependency behavior (CONCEPT:OBJ-1.5).

The core install must import cleanly with zero cloud SDKs, and each cloud
backend must fail with a clear, actionable message naming its pip extra.
Blocking ``sys.modules`` entries makes these tests deterministic whether or
not the SDKs happen to be installed.
"""

import sys

import pytest

from objectstore_mcp.api.api_client_base import MissingDependencyError


@pytest.fixture
def block_module(monkeypatch):
    def _block(name: str):
        monkeypatch.setitem(sys.modules, name, None)
        for mod in list(sys.modules):
            if mod == name or mod.startswith(f"{name}."):
                if sys.modules[mod] is not None:
                    monkeypatch.setitem(sys.modules, mod, None)

    return _block


def test_core_package_imports_without_cloud_sdks():
    import objectstore_mcp
    import objectstore_mcp.api
    import objectstore_mcp.mcp.mcp_objectstore  # noqa: F401

    assert objectstore_mcp.__version__


def test_s3_backend_names_its_extra(block_module):
    block_module("boto3")
    from objectstore_mcp.api.api_client_s3 import S3Backend

    with pytest.raises(MissingDependencyError, match=r"objectstore-mcp\[s3\]"):
        S3Backend()


def test_gcs_backend_names_its_extra(block_module):
    block_module("google")
    from objectstore_mcp.api.api_client_gcs import GCSBackend

    with pytest.raises(MissingDependencyError, match=r"objectstore-mcp\[gcs\]"):
        GCSBackend()


def test_azure_backend_names_its_extra(block_module):
    block_module("azure")
    from objectstore_mcp.api.api_client_azure_blob import AzureBlobBackend

    with pytest.raises(MissingDependencyError, match=r"objectstore-mcp\[azure\]"):
        AzureBlobBackend()


def test_injected_clients_bypass_sdk_requirement(block_module):
    """Backends accept injected clients even with no SDK importable."""
    block_module("boto3")
    block_module("google")
    block_module("azure")
    from objectstore_mcp.api.api_client_azure_blob import AzureBlobBackend
    from objectstore_mcp.api.api_client_gcs import GCSBackend
    from objectstore_mcp.api.api_client_s3 import S3Backend

    sentinel = object()
    assert S3Backend(client=sentinel).client is sentinel
    assert GCSBackend(client=sentinel).client is sentinel
    assert AzureBlobBackend(client=sentinel).client is sentinel
