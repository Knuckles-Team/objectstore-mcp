"""End-to-end MCP tool tests over the in-memory FastMCP client.

These exercise the real tool layer (action routing, store resolution, size
caps, encodings) against the real filesystem backend — no mocks anywhere.
"""

import base64
import json

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from objectstore_mcp.mcp.mcp_objectstore import register_objectstore_tools


@pytest.fixture
def mcp(local_store_env):
    server = FastMCP("objectstore-test")
    register_objectstore_tools(server)
    return server


def payload(result):
    if getattr(result, "data", None) is not None:
        return result.data
    return json.loads(result.content[0].text)


async def call(mcp, tool, action, params=None, store=None):
    async with Client(mcp) as client:
        arguments = {"action": action, "params_json": json.dumps(params or {})}
        if store is not None:
            arguments["store"] = store
        return payload(await client.call_tool(tool, arguments))


async def test_tool_inventory(mcp):
    async with Client(mcp) as client:
        tools = {t.name for t in await client.list_tools()}
    assert tools == {"objects", "buckets", "transfer"}


async def test_bucket_lifecycle(mcp):
    created = await call(mcp, "buckets", "create", {"bucket": "alpha"})
    assert created["name"] == "alpha"
    exists = await call(mcp, "buckets", "exists", {"bucket": "alpha"})
    assert exists["exists"] is True
    listing = await call(mcp, "buckets", "list")
    assert [b["name"] for b in listing["buckets"]] == ["alpha"]
    info = await call(mcp, "buckets", "info", {"bucket": "alpha"})
    assert info["capabilities"]["presigned_urls"] is False


async def test_stores_action(mcp):
    stores = await call(mcp, "buckets", "stores")
    assert "local" in stores
    assert stores["local"]["backend"] == "filesystem"


async def test_put_get_text_and_base64(mcp):
    await call(mcp, "buckets", "create", {"bucket": "data"})
    put = await call(
        mcp,
        "objects",
        "put",
        {
            "bucket": "data",
            "key": "notes/hello.txt",
            "text": "hello world",
            "content_type": "text/plain",
            "metadata": {"owner": "ops"},
        },
    )
    assert put["size"] == 11

    got = await call(mcp, "objects", "get", {"bucket": "data", "key": "notes/hello.txt"})
    assert got == {
        "bucket": "data",
        "key": "notes/hello.txt",
        "size": 11,
        "encoding": "text",
        "content": "hello world",
    }

    binary = bytes(range(256))
    await call(
        mcp,
        "objects",
        "put",
        {
            "bucket": "data",
            "key": "blob.bin",
            "content_base64": base64.b64encode(binary).decode(),
        },
    )
    got = await call(mcp, "objects", "get", {"bucket": "data", "key": "blob.bin"})
    assert got["encoding"] == "base64"
    assert base64.b64decode(got["content"]) == binary

    head = await call(mcp, "objects", "head", {"bucket": "data", "key": "blob.bin"})
    assert head["size"] == 256


async def test_list_with_pagination(mcp):
    await call(mcp, "buckets", "create", {"bucket": "data"})
    for i in range(5):
        await call(
            mcp, "objects", "put", {"bucket": "data", "key": f"k{i}", "text": "x"}
        )
    page = await call(
        mcp, "objects", "list", {"bucket": "data", "max_keys": 3}
    )
    assert len(page["objects"]) == 3 and page["truncated"]
    rest = await call(
        mcp,
        "objects",
        "list",
        {"bucket": "data", "max_keys": 3, "token": page["next_token"]},
    )
    assert len(rest["objects"]) == 2 and not rest["truncated"]


async def test_copy_move_delete(mcp):
    await call(mcp, "buckets", "create", {"bucket": "data"})
    await call(mcp, "objects", "put", {"bucket": "data", "key": "a", "text": "1"})

    copied = await call(
        mcp,
        "objects",
        "copy",
        {"bucket": "data", "key": "a", "dest_key": "b"},
    )
    assert copied["dest"]["key"] == "b"

    moved = await call(
        mcp,
        "objects",
        "move",
        {"bucket": "data", "key": "a", "dest_key": "c"},
    )
    assert moved["dest"]["key"] == "c"
    with pytest.raises(ToolError, match="not"):
        await call(mcp, "objects", "head", {"bucket": "data", "key": "a"})

    deleted = await call(mcp, "objects", "delete", {"bucket": "data", "key": "c"})
    assert deleted["deleted"] is True


async def test_metadata_actions(mcp):
    await call(mcp, "buckets", "create", {"bucket": "data"})
    await call(mcp, "objects", "put", {"bucket": "data", "key": "k", "text": "x"})
    await call(
        mcp,
        "objects",
        "metadata_set",
        {"bucket": "data", "key": "k", "metadata": {"env": "prod"}},
    )
    got = await call(mcp, "objects", "metadata_get", {"bucket": "data", "key": "k"})
    assert got["metadata"] == {"env": "prod"}


async def test_presign_unsupported_on_filesystem(mcp):
    await call(mcp, "buckets", "create", {"bucket": "data"})
    await call(mcp, "objects", "put", {"bucket": "data", "key": "k", "text": "x"})
    with pytest.raises(ToolError, match="presigned"):
        await call(mcp, "objects", "presign", {"bucket": "data", "key": "k"})


async def test_unknown_action_and_store(mcp):
    with pytest.raises(ToolError, match="Unknown objects action"):
        await call(mcp, "objects", "explode", {})
    with pytest.raises(ToolError, match="Unknown store"):
        await call(mcp, "buckets", "list", store="ghost")


async def test_named_store_routing(mcp, tmp_path, monkeypatch):
    monkeypatch.setenv(
        "OBJECTSTORE_STORES",
        json.dumps(
            {"scratch": {"backend": "filesystem", "root": str(tmp_path / "scratch")}}
        ),
    )
    await call(mcp, "buckets", "create", {"bucket": "b"}, store="scratch")
    await call(
        mcp, "objects", "put", {"bucket": "b", "key": "k", "text": "x"}, store="scratch"
    )
    assert (tmp_path / "scratch" / "b" / "k").read_text() == "x"
    # The default store (local) does not see scratch's bucket.
    local = await call(mcp, "buckets", "list", store="local")
    assert local["buckets"] == []


async def test_transfer_roundtrip(mcp, tmp_path):
    await call(mcp, "buckets", "create", {"bucket": "data"})
    src = tmp_path / "in.txt"
    src.write_text("payload")
    uploaded = await call(
        mcp,
        "transfer",
        "upload",
        {"bucket": "data", "local_path": str(src), "key": "in.txt"},
    )
    assert uploaded["size"] == 7

    dst = tmp_path / "out" / "result.txt"
    downloaded = await call(
        mcp,
        "transfer",
        "download",
        {"bucket": "data", "key": "in.txt", "local_path": str(dst)},
    )
    assert downloaded["size"] == 7
    assert dst.read_text() == "payload"

    with pytest.raises(ToolError, match="overwrite"):
        await call(
            mcp,
            "transfer",
            "download",
            {"bucket": "data", "key": "in.txt", "local_path": str(dst)},
        )


async def test_transfer_directory_roundtrip(mcp, tmp_path):
    await call(mcp, "buckets", "create", {"bucket": "data"})
    src_dir = tmp_path / "tree"
    (src_dir / "sub").mkdir(parents=True)
    (src_dir / "a.txt").write_text("a")
    (src_dir / "sub" / "b.txt").write_text("b")

    uploaded = await call(
        mcp,
        "transfer",
        "upload_dir",
        {"bucket": "data", "local_dir": str(src_dir), "prefix": "backup/"},
    )
    assert uploaded["uploaded"] == ["backup/a.txt", "backup/sub/b.txt"]

    out_dir = tmp_path / "restore"
    downloaded = await call(
        mcp,
        "transfer",
        "download_prefix",
        {"bucket": "data", "prefix": "backup/", "local_dir": str(out_dir)},
    )
    assert downloaded["count"] == 2
    assert (out_dir / "a.txt").read_text() == "a"
    assert (out_dir / "sub" / "b.txt").read_text() == "b"
