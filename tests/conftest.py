"""Shared fixtures: isolated filesystem stores and clean env/caches."""

import pytest
from scion_sdk.storage import FilesystemBackend

from objectstore_mcp.auth import reset_backend_cache

ENV_VARS = [
    "OBJECTSTORE_STORES",
    "OBJECTSTORE_DEFAULT_STORE",
    "OBJECTSTORE_FS_ROOT",
    "OBJECTSTORE_MAX_GET_BYTES",
    "OBJECTSTORE_MAX_PUT_BYTES",
    "OBJECTSTORE_MAX_TRANSFER_BYTES",
    "OBJECTSTORE_MAX_BATCH_KEYS",
    "OBJECTSTORE_MAX_LIST_KEYS",
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


@pytest.fixture
def mcp(local_store_env):
    """The served tool surface: SDK per-operation tools plus the typed tools."""
    from scion_sdk.connector import build_server

    _args, server = build_server("objectstore_mcp", command_args=[])
    return server


def tool_payload(result):
    """A tool result as plain data (structured content or decoded text)."""
    import json

    if getattr(result, "data", None) is not None:
        return result.data
    if getattr(result, "structured_content", None) is not None:
        return result.structured_content
    if not result.content:
        return None
    text = result.content[0].text
    try:
        return json.loads(text)
    except ValueError:
        return text


async def call_tool(server, tool, **arguments):
    """Call one tool over the in-memory client and return its payload."""
    from fastmcp import Client

    async with Client(server) as client:
        return tool_payload(await client.call_tool(tool, arguments))


def _tool_failures():
    from fastmcp.exceptions import ToolError
    from mcp.shared.exceptions import MCPError

    return (ToolError, MCPError)


#: A refused tool call surfaces as either error type over the in-memory client.
ToolFailure = _tool_failures()
