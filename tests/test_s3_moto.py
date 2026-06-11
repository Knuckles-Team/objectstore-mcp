"""Same S3 flows against moto's in-process S3 (needs the ``test-s3`` extra).

Skipped automatically when moto/boto3 are not installed; the fake-client
tests in ``test_s3_backend.py`` cover the backend either way.
"""

import pytest

moto = pytest.importorskip("moto", reason="moto not installed (test-s3 extra)")
boto3 = pytest.importorskip("boto3", reason="boto3 not installed (s3 extra)")

from objectstore_mcp.backends.base import NotFoundError  # noqa: E402
from objectstore_mcp.backends.s3 import S3Backend  # noqa: E402


@pytest.fixture
def backend(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    with moto.mock_aws():
        yield S3Backend(client=boto3.client("s3", region_name="us-east-1"))


def test_roundtrip(backend):
    backend.create_bucket("data")
    backend.put_object("data", "k.txt", b"hello", content_type="text/plain")
    assert backend.get_object("data", "k.txt") == b"hello"
    assert backend.head_object("data", "k.txt").size == 5
    page = backend.list_objects("data")
    assert [o.key for o in page.objects] == ["k.txt"]
    backend.delete_object("data", "k.txt")
    backend.delete_bucket("data")


def test_not_found_translation(backend):
    backend.create_bucket("data")
    with pytest.raises(NotFoundError):
        backend.head_object("data", "ghost")


def test_presigned_url(backend):
    backend.create_bucket("data")
    backend.put_object("data", "k", b"x")
    url = backend.presigned_url("data", "k", method="GET", expires_in=120)
    assert url.startswith("https://") and "k" in url
