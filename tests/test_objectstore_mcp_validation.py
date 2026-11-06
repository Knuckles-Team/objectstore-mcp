"""End-to-end MCP tool tests over the in-memory FastMCP client (CONN-OBJECTSTORE-MCP-R005).

They run the served surface (SDK per-operation tools plus the typed tools)
against the real filesystem backend, and the S3 management tools against a
recording client.
"""

import json

import pytest
from tests.conftest import ToolFailure
from tests.conftest import call_tool as call
from fastmcp import Client

from objectstore_mcp.auth import get_backend
from objectstore_mcp.guard import GuardedBackend


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R005")
async def test_tool_inventory_is_typed_with_no_action_routing(mcp):
    async with Client(mcp) as client:
        tools = await client.list_tools()
    names = {t.name for t in tools}
    assert {
        "objectstore_list_buckets",
        "objectstore_put_object",
        "objectstore_presigned_url",
        "objectstore_list_stores",
        "objectstore_move_object",
        "objectstore_delete_objects_by_prefix",
        "objectstore_upload_file",
        "objectstore_download_prefix",
        "objectstore_get_bucket_lifecycle",
        "objectstore_put_bucket_lifecycle",
        "objectstore_delete_bucket_lifecycle",
        "objectstore_get_bucket_versioning",
        "objectstore_put_bucket_versioning",
        "objectstore_get_object_tags",
        "objectstore_put_object_tags",
        "objectstore_delete_object_tags",
        "objectstore_ingest_buckets",
        "objectstore_ingest_objects",
    } <= names
    for tool in tools:
        props = tool.inputSchema.get("properties") or {}
        assert "action" not in props and "params_json" not in props, tool.name
        assert "split-action" not in ((tool.meta or {}).get("fastmcp") or {}).get(
            "tags", []
        ), tool.name


async def test_bucket_and_object_crud(mcp):
    created = await call(mcp, "objectstore_create_bucket", bucket="alpha")
    assert created["name"] == "alpha"
    assert await call(mcp, "objectstore_bucket_exists", bucket="alpha") is True
    listing = await call(mcp, "objectstore_list_buckets")
    names = [b["name"] for b in (listing.get("result", listing) if isinstance(listing, dict) else listing)]
    assert names == ["alpha"]
    await call(
        mcp,
        "objectstore_put_object",
        bucket="alpha",
        key="docs/a.txt",
        data="hello",
        content_type="text/plain",
    )
    head = await call(mcp, "objectstore_head_object", bucket="alpha", key="docs/a.txt")
    assert head["size"] == 5
    await call(
        mcp,
        "objectstore_copy_object",
        src_bucket="alpha",
        src_key="docs/a.txt",
        dst_bucket="alpha",
        dst_key="docs/b.txt",
    )
    moved = await call(
        mcp,
        "objectstore_move_object",
        src_bucket="alpha",
        src_key="docs/b.txt",
        dst_bucket="alpha",
        dst_key="docs/c.txt",
    )
    assert moved["dest"]["key"] == "docs/c.txt"
    page = await call(mcp, "objectstore_list_objects", bucket="alpha", prefix="docs/")
    assert [o["key"] for o in page["objects"]] == ["docs/a.txt", "docs/c.txt"]
    await call(
        mcp, "objectstore_delete_object", bucket="alpha", key="docs/c.txt", confirm=True
    )


async def test_list_stores_and_named_store_routing(mcp, tmp_path, monkeypatch):
    monkeypatch.setenv(
        "OBJECTSTORE_STORES",
        json.dumps({"scratch": {"backend": "filesystem", "root": str(tmp_path / "s")}}),
    )
    stores = await call(mcp, "objectstore_list_stores")
    assert set(stores) == {"local", "scratch"}
    tree = tmp_path / "in"
    tree.mkdir()
    (tree / "f.txt").write_text("x")
    backend, _ = get_backend("scratch")
    backend.create_bucket("b")
    await call(
        mcp,
        "objectstore_upload_file",
        bucket="b",
        local_path=str(tree / "f.txt"),
        store="scratch",
    )
    assert (tmp_path / "s" / "b" / "f.txt").read_text() == "x"
    with pytest.raises(ToolFailure, match="Unknown store"):
        await call(mcp, "objectstore_ingest_buckets", store="ghost")


async def test_transfer_roundtrip(mcp, tmp_path):
    await call(mcp, "objectstore_create_bucket", bucket="data")
    tree = tmp_path / "tree"
    (tree / "sub").mkdir(parents=True)
    (tree / "a.txt").write_text("a")
    (tree / "sub" / "b.txt").write_text("b")
    up = await call(
        mcp,
        "objectstore_upload_directory",
        bucket="data",
        local_dir=str(tree),
        prefix="backup/",
    )
    assert up["uploaded"] == ["backup/a.txt", "backup/sub/b.txt"]
    out = tmp_path / "restore"
    down = await call(
        mcp,
        "objectstore_download_prefix",
        bucket="data",
        prefix="backup/",
        local_dir=str(out),
    )
    assert down["count"] == 2 and (out / "sub" / "b.txt").read_text() == "b"
    dst = tmp_path / "one.txt"
    await call(
        mcp,
        "objectstore_download_file",
        bucket="data",
        key="backup/a.txt",
        local_path=str(dst),
    )
    with pytest.raises(ToolFailure, match="overwrite"):
        await call(
            mcp,
            "objectstore_download_file",
            bucket="data",
            key="backup/a.txt",
            local_path=str(dst),
        )


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R007")
async def test_s3_management_refuses_on_filesystem_store(mcp):
    await call(mcp, "objectstore_create_bucket", bucket="data")
    with pytest.raises(ToolFailure, match="does not support"):
        await call(mcp, "objectstore_get_bucket_lifecycle", bucket="data")


class _RecordingS3:
    """Stands in for the boto3 client of an S3 store."""

    backend_type = "s3"

    def __init__(self):
        self.calls = []
        self.client = self
        self.lifecycle = None
        self.tags = []

    def put_bucket_lifecycle_configuration(self, Bucket, LifecycleConfiguration):
        self.calls.append(("put_lc", Bucket))
        self.lifecycle = LifecycleConfiguration

    def get_bucket_lifecycle_configuration(self, Bucket):
        if self.lifecycle is None:
            error = Exception("absent")
            error.response = {"Error": {"Code": "NoSuchLifecycleConfiguration"}}
            raise error
        return self.lifecycle

    def delete_bucket_lifecycle(self, Bucket):
        self.lifecycle = None

    def get_bucket_versioning(self, Bucket):
        return {"Status": "Enabled"}

    def put_bucket_versioning(self, Bucket, VersioningConfiguration):
        self.calls.append(("versioning", VersioningConfiguration["Status"]))

    def put_object_tagging(self, Bucket, Key, Tagging):
        self.tags = Tagging["TagSet"]

    def get_object_tagging(self, Bucket, Key):
        return {"TagSet": self.tags}

    def delete_object_tagging(self, Bucket, Key):
        self.tags = []


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R007")
async def test_s3_lifecycle_versioning_and_tags(mcp, monkeypatch):
    from objectstore_mcp import auth

    fake = _RecordingS3()
    monkeypatch.setitem(auth._BACKEND_CACHE, "local", GuardedBackend(fake))
    assert (await call(mcp, "objectstore_get_bucket_lifecycle", bucket="m"))[
        "rules"
    ] == []
    await call(
        mcp,
        "objectstore_put_bucket_lifecycle",
        bucket="m",
        rules=[
            {"id": "scratch", "prefix": "scratch/", "expiration_days": 7},
            {"id": "old", "prefix": "", "noncurrent_expiration_days": 30},
        ],
    )
    s3_rules = fake.lifecycle["Rules"]
    assert s3_rules[0]["Expiration"] == {"Days": 7}
    assert s3_rules[1]["NoncurrentVersionExpiration"] == {"NoncurrentDays": 30}
    got = await call(mcp, "objectstore_get_bucket_lifecycle", bucket="m")
    assert [r["id"] for r in got["rules"]] == ["scratch", "old"]
    await call(mcp, "objectstore_delete_bucket_lifecycle", bucket="m")
    assert fake.lifecycle is None
    with pytest.raises(ToolFailure, match="sets no action"):
        await call(
            mcp, "objectstore_put_bucket_lifecycle", bucket="m", rules=[{"id": "x"}]
        )
    assert (await call(mcp, "objectstore_get_bucket_versioning", bucket="m"))[
        "status"
    ] == "Enabled"
    await call(mcp, "objectstore_put_bucket_versioning", bucket="m", status="Suspended")
    assert ("versioning", "Suspended") in fake.calls
    await call(mcp, "objectstore_put_object_tags", bucket="m", key="k", tags={"a": "1"})
    assert (await call(mcp, "objectstore_get_object_tags", bucket="m", key="k"))[
        "tags"
    ] == {"a": "1"}
    await call(mcp, "objectstore_delete_object_tags", bucket="m", key="k")
    assert fake.tags == []


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R005")
def test_refusal_keeps_the_storage_cause(monkeypatch):
    from objectstore_mcp.auth import get_client, reset_backend_cache

    monkeypatch.setenv(
        "OBJECTSTORE_STORES",
        json.dumps({"s": {"backend": "s3", "endpoint": "http://storage.internal.example"}}),
    )
    monkeypatch.setenv("OBJECTSTORE_DEFAULT_STORE", "s")
    reset_backend_cache()
    with pytest.raises(RuntimeError, match=r"AUTHENTICATION ERROR: STORAGE_\w+: \S+"):
        get_client()
