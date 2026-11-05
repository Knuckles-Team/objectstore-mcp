"""CONN-OBJECTSTORE-MCP: every store runs through the SDK storage backends."""

import json
import re
import tomllib
from pathlib import Path

import pytest
from scion_sdk.storage import UnsupportedOperationError, WebDavBackend

from objectstore_mcp.auth import get_backend, reset_backend_cache

ROOT = Path(__file__).resolve().parent.parent
RETIRED = re.compile(r"agent[-_]connector[-_]sdk")


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R001")
def test_tools_route_through_sdk_backends_and_no_local_copy(local_store_env):
    backend, config = get_backend("local")
    assert type(backend).__module__.startswith("scion_sdk.storage.")
    backend.create_bucket("data")
    backend.put_object("data", "k.txt", b"hello")
    assert backend.get_object("data", "k.txt") == b"hello"
    for module in (ROOT / "objectstore_mcp" / "api").glob("*.py"):
        assert "backend_type" not in module.read_text(encoding="utf-8")


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R002")
def test_extras_name_the_sdk_storage_extras():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    extras = project["optional-dependencies"]
    for name, sdk_extra in (
        ("s3", "storage-s3"),
        ("gcs", "storage-gcs"),
        ("azure", "storage-azure"),
    ):
        assert len(extras[name]) == 1
        assert f"scion-sdk[{sdk_extra}]" in extras[name][0]
    pins = " ".join(project["dependencies"] + sum(extras.values(), []))
    for provider in ("boto3", "google-cloud-storage", "azure-storage-blob"):
        assert provider not in pins


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R003")
def test_webdav_store_routes_through_sdk(monkeypatch):
    monkeypatch.setenv("SHARE_USER", "svc")
    monkeypatch.setenv("SHARE_PASS", "pw")
    monkeypatch.setenv(
        "OBJECTSTORE_STORES",
        json.dumps(
            {
                "share": {
                    "backend": "webdav",
                    "endpoint": "http://127.0.0.1:8080/dav/files/svc",
                    "credentials": {
                        "username": "env://SHARE_USER",
                        "password": "env://SHARE_PASS",
                    },
                }
            }
        ),
    )
    reset_backend_cache()
    backend, _config = get_backend("share")
    assert isinstance(backend, WebDavBackend)
    with pytest.raises(UnsupportedOperationError) as excinfo:
        backend.presigned_url("bucket", "key")
    assert excinfo.value.code == "STORAGE_UNSUPPORTED"


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R004")
def test_no_retired_sdk_name_in_package_or_docs():
    paths = [ROOT / "AGENTS.md", ROOT / "README.md"]
    paths += list((ROOT / "objectstore_mcp").rglob("*.py"))
    paths += list((ROOT / "docs").rglob("*.md"))
    hits = [
        p
        for p in paths
        if p.is_file() and RETIRED.search(p.read_text(encoding="utf-8"))
    ]
    assert hits == []
