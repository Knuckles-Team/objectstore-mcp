"""Safety-governor tests (CONN-OBJECTSTORE-MCP-R006, CONCEPT:OB-OS.safety.size-caps-list-batch).

Caps, destructive-operation flags, dry runs and explicitness hold on every tool,
including the per-operation tools the SDK generates from the backend protocol.
"""

import pytest
from tests.conftest import ToolFailure
from tests.conftest import call_tool as call


async def seed(mcp, keys=("tmp/a", "tmp/b", "keep/c")):
    await call(mcp, "objectstore_create_bucket", bucket="data")
    for key in keys:
        await call(mcp, "objectstore_put_object", bucket="data", key=key, data="x")


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R006")
async def test_put_cap_enforced(mcp, monkeypatch):
    monkeypatch.setenv("OBJECTSTORE_MAX_PUT_BYTES", "4")
    await call(mcp, "objectstore_create_bucket", bucket="data")
    with pytest.raises(ToolFailure, match="put cap"):
        await call(mcp, "objectstore_put_object", bucket="data", key="k", data="too long")


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R006")
async def test_get_cap_enforced(mcp, monkeypatch):
    await seed(mcp)
    monkeypatch.setenv("OBJECTSTORE_MAX_GET_BYTES", "0")
    with pytest.raises(ToolFailure):
        await call(mcp, "objectstore_get_object", bucket="data", key="tmp/a")
    # A caller cannot raise the cap above the configured limit.
    with pytest.raises(ToolFailure):
        await call(
            mcp, "objectstore_get_object", bucket="data", key="tmp/a", max_bytes=999999
        )


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R006")
async def test_list_cap_clamped(mcp, monkeypatch):
    monkeypatch.setenv("OBJECTSTORE_MAX_LIST_KEYS", "2")
    await seed(mcp)
    page = await call(mcp, "objectstore_list_objects", bucket="data", max_keys=50)
    assert len(page["objects"]) == 2 and page["truncated"]


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R006")
async def test_delete_rejects_wildcards(mcp):
    await seed(mcp)
    for key in ("tmp/*", "tmp/?"):
        with pytest.raises(ToolFailure, match="wildcard"):
            await call(
                mcp, "objectstore_delete_object", bucket="data", key=key, confirm=True
            )


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R006")
async def test_delete_flag_blocks_objects(mcp, monkeypatch):
    await seed(mcp)
    monkeypatch.setenv("OBJECTSTORE_ALLOW_DELETE", "false")
    with pytest.raises(ToolFailure, match="disabled"):
        await call(
            mcp, "objectstore_delete_object", bucket="data", key="tmp/a", confirm=True
        )
    with pytest.raises(ToolFailure, match="disabled"):
        await call(
            mcp, "objectstore_delete_objects_by_prefix", bucket="data", prefix="tmp/"
        )
    with pytest.raises(ToolFailure, match="disabled"):
        await call(
            mcp,
            "objectstore_move_object",
            src_bucket="data",
            src_key="tmp/a",
            dst_bucket="data",
            dst_key="z",
        )


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R006")
async def test_delete_by_prefix_dry_run_by_default(mcp):
    await seed(mcp)
    preview = await call(
        mcp, "objectstore_delete_objects_by_prefix", bucket="data", prefix="tmp/"
    )
    assert (preview["dry_run"], preview["matched"], preview["deleted"]) == (True, 2, 0)
    page = await call(mcp, "objectstore_list_objects", bucket="data", prefix="tmp/")
    assert len(page["objects"]) == 2


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R006")
async def test_delete_by_prefix_executes_with_dry_run_false(mcp):
    await seed(mcp)
    result = await call(
        mcp,
        "objectstore_delete_objects_by_prefix",
        bucket="data",
        prefix="tmp/",
        dry_run=False,
    )
    assert result["deleted"] == 2
    page = await call(mcp, "objectstore_list_objects", bucket="data")
    assert [o["key"] for o in page["objects"]] == ["keep/c"]


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R006")
async def test_delete_by_prefix_requires_prefix(mcp):
    await seed(mcp)
    with pytest.raises(ToolFailure, match="prefix"):
        await call(mcp, "objectstore_delete_objects_by_prefix", bucket="data", prefix="")


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R006")
async def test_delete_by_prefix_capped(mcp, monkeypatch):
    monkeypatch.setenv("OBJECTSTORE_MAX_BATCH_KEYS", "1")
    await seed(mcp)
    result = await call(
        mcp,
        "objectstore_delete_objects_by_prefix",
        bucket="data",
        prefix="tmp/",
        max_keys=50,
    )
    assert result["matched"] == 1 and result["truncated"]


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R006")
async def test_bucket_delete_disabled_by_default(mcp):
    await call(mcp, "objectstore_create_bucket", bucket="data")
    with pytest.raises(ToolFailure, match="disabled"):
        await call(mcp, "objectstore_delete_bucket", bucket="data", confirm=True)


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R006")
async def test_bucket_delete_opt_in_and_empty_only(mcp, monkeypatch):
    monkeypatch.setenv("OBJECTSTORE_ALLOW_BUCKET_DELETE", "true")
    await seed(mcp)
    with pytest.raises(ToolFailure):
        await call(mcp, "objectstore_delete_bucket", bucket="data", confirm=True)
    await call(mcp, "objectstore_create_bucket", bucket="empty")
    await call(mcp, "objectstore_delete_bucket", bucket="empty", confirm=True)
    assert not await call(mcp, "objectstore_bucket_exists", bucket="empty")


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R006")
async def test_transfer_caps(mcp, tmp_path, monkeypatch):
    monkeypatch.setenv("OBJECTSTORE_MAX_TRANSFER_BYTES", "3")
    await call(mcp, "objectstore_create_bucket", bucket="data")
    src = tmp_path / "big.bin"
    src.write_bytes(b"12345")
    with pytest.raises(ToolFailure, match="transfer cap"):
        await call(mcp, "objectstore_upload_file", bucket="data", local_path=str(src))


@pytest.mark.spec("CONN-OBJECTSTORE-MCP-R006")
async def test_upload_directory_batch_cap(mcp, tmp_path, monkeypatch):
    monkeypatch.setenv("OBJECTSTORE_MAX_BATCH_KEYS", "1")
    await call(mcp, "objectstore_create_bucket", bucket="data")
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "a").write_text("a")
    (tree / "b").write_text("b")
    with pytest.raises(ToolFailure, match="batch cap"):
        await call(
            mcp, "objectstore_upload_directory", bucket="data", local_dir=str(tree)
        )
