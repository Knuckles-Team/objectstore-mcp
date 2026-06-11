"""Safety-governor tests (CONCEPT:OBJ-1.3): caps, flags, dry-run, explicitness."""

import json

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from objectstore_mcp.mcp.mcp_objectstore import register_objectstore_tools


@pytest.fixture
def mcp(local_store_env):
    server = FastMCP("objectstore-safety-test")
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


async def seed(mcp, keys=("tmp/a", "tmp/b", "keep/c")):
    await call(mcp, "buckets", "create", {"bucket": "data"})
    for key in keys:
        await call(mcp, "objects", "put", {"bucket": "data", "key": key, "text": "x"})


async def test_put_cap_enforced(mcp, monkeypatch):
    monkeypatch.setenv("OBJECTSTORE_MAX_PUT_BYTES", "4")
    await call(mcp, "buckets", "create", {"bucket": "data"})
    with pytest.raises(ToolError, match="put cap"):
        await call(
            mcp, "objects", "put", {"bucket": "data", "key": "k", "text": "too long"}
        )


async def test_get_cap_enforced(mcp, monkeypatch):
    await seed(mcp)
    monkeypatch.setenv("OBJECTSTORE_MAX_GET_BYTES", "0")
    with pytest.raises(ToolError, match="cap"):
        await call(mcp, "objects", "get", {"bucket": "data", "key": "tmp/a"})
    # A caller cannot raise the cap above the configured limit.
    with pytest.raises(ToolError, match="cap"):
        await call(
            mcp,
            "objects",
            "get",
            {"bucket": "data", "key": "tmp/a", "max_bytes": 999999},
        )


async def test_list_cap_clamped(mcp, monkeypatch):
    monkeypatch.setenv("OBJECTSTORE_MAX_LIST_KEYS", "2")
    await seed(mcp)
    page = await call(
        mcp, "objects", "list", {"bucket": "data", "max_keys": 50}
    )
    assert len(page["objects"]) == 2 and page["truncated"]


async def test_delete_requires_explicit_bucket_and_key(mcp):
    await seed(mcp)
    with pytest.raises(ToolError, match="explicit"):
        await call(mcp, "objects", "delete", {"key": "tmp/a"})
    with pytest.raises(ToolError, match="explicit"):
        await call(mcp, "objects", "delete", {"bucket": "data"})


async def test_delete_rejects_wildcards(mcp):
    await seed(mcp)
    with pytest.raises(ToolError, match="wildcard"):
        await call(mcp, "objects", "delete", {"bucket": "data", "key": "tmp/*"})
    with pytest.raises(ToolError, match="wildcard"):
        await call(mcp, "objects", "delete", {"bucket": "data", "key": "tmp/?"})


async def test_delete_flag_blocks_objects(mcp, monkeypatch):
    await seed(mcp)
    monkeypatch.setenv("OBJECTSTORE_ALLOW_DELETE", "false")
    with pytest.raises(ToolError, match="disabled"):
        await call(mcp, "objects", "delete", {"bucket": "data", "key": "tmp/a"})
    with pytest.raises(ToolError, match="disabled"):
        await call(mcp, "objects", "delete_batch", {"bucket": "data", "prefix": "tmp/"})
    with pytest.raises(ToolError, match="disabled"):
        await call(mcp, "objects", "move", {"bucket": "data", "key": "tmp/a", "dest_key": "z"})


async def test_delete_batch_dry_run_by_default(mcp):
    await seed(mcp)
    preview = await call(
        mcp, "objects", "delete_batch", {"bucket": "data", "prefix": "tmp/"}
    )
    assert preview["dry_run"] is True
    assert preview["matched"] == 2
    assert preview["deleted"] == 0
    # Nothing was actually deleted.
    page = await call(mcp, "objects", "list", {"bucket": "data", "prefix": "tmp/"})
    assert len(page["objects"]) == 2


async def test_delete_batch_executes_with_dry_run_false(mcp):
    await seed(mcp)
    result = await call(
        mcp,
        "objects",
        "delete_batch",
        {"bucket": "data", "prefix": "tmp/", "dry_run": False},
    )
    assert result["deleted"] == 2
    page = await call(mcp, "objects", "list", {"bucket": "data"})
    assert [o["key"] for o in page["objects"]] == ["keep/c"]


async def test_delete_batch_requires_prefix(mcp):
    await seed(mcp)
    with pytest.raises(ToolError, match="prefix"):
        await call(mcp, "objects", "delete_batch", {"bucket": "data"})
    with pytest.raises(ToolError, match="prefix"):
        await call(mcp, "objects", "delete_batch", {"bucket": "data", "prefix": ""})


async def test_delete_batch_capped(mcp, monkeypatch):
    monkeypatch.setenv("OBJECTSTORE_MAX_BATCH_KEYS", "1")
    await seed(mcp)
    result = await call(
        mcp,
        "objects",
        "delete_batch",
        {"bucket": "data", "prefix": "tmp/", "max_keys": 50, "dry_run": False},
    )
    assert result["deleted"] == 1
    assert result["truncated"] is True


async def test_bucket_delete_disabled_by_default(mcp):
    await call(mcp, "buckets", "create", {"bucket": "doomed"})
    with pytest.raises(ToolError, match="OBJECTSTORE_ALLOW_BUCKET_DELETE"):
        await call(mcp, "buckets", "delete", {"bucket": "doomed"})


async def test_bucket_delete_opt_in_and_empty_only(mcp, monkeypatch):
    monkeypatch.setenv("OBJECTSTORE_ALLOW_BUCKET_DELETE", "true")
    await seed(mcp)
    with pytest.raises(ToolError, match="not empty"):
        await call(mcp, "buckets", "delete", {"bucket": "data"})
    await call(mcp, "buckets", "create", {"bucket": "empty"})
    result = await call(mcp, "buckets", "delete", {"bucket": "empty"})
    assert result["deleted"] is True


async def test_transfer_caps(mcp, tmp_path, monkeypatch):
    monkeypatch.setenv("OBJECTSTORE_MAX_TRANSFER_BYTES", "4")
    await call(mcp, "buckets", "create", {"bucket": "data"})
    big = tmp_path / "big.bin"
    big.write_bytes(b"x" * 100)
    with pytest.raises(ToolError, match="transfer cap"):
        await call(
            mcp, "transfer", "upload", {"bucket": "data", "local_path": str(big)}
        )


async def test_upload_dir_batch_cap(mcp, tmp_path, monkeypatch):
    monkeypatch.setenv("OBJECTSTORE_MAX_BATCH_KEYS", "1")
    await call(mcp, "buckets", "create", {"bucket": "data"})
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "a.txt").write_text("a")
    (tree / "b.txt").write_text("b")
    with pytest.raises(ToolError, match="batch cap"):
        await call(
            mcp, "transfer", "upload_dir", {"bucket": "data", "local_dir": str(tree)}
        )


async def test_put_rejects_ambiguous_and_bad_payloads(mcp):
    await call(mcp, "buckets", "create", {"bucket": "data"})
    with pytest.raises(ToolError, match="not both"):
        await call(
            mcp,
            "objects",
            "put",
            {"bucket": "data", "key": "k", "text": "x", "content_base64": "eA=="},
        )
    with pytest.raises(ToolError, match="base64"):
        await call(
            mcp,
            "objects",
            "put",
            {"bucket": "data", "key": "k", "content_base64": "!!!not-base64!!!"},
        )
    with pytest.raises(ToolError, match="text"):
        await call(mcp, "objects", "put", {"bucket": "data", "key": "k"})


async def test_get_text_mode_rejects_binary(mcp):
    await call(mcp, "buckets", "create", {"bucket": "data"})
    await call(
        mcp,
        "objects",
        "put",
        {"bucket": "data", "key": "bin", "content_base64": "/wD/AA=="},
    )
    with pytest.raises(ToolError, match="base64"):
        await call(
            mcp, "objects", "get", {"bucket": "data", "key": "bin", "mode": "text"}
        )
