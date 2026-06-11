"""Server bootstrap: the FastMCP instance builds and registers the tools."""

import sys
from unittest.mock import patch


def test_get_mcp_instance_registers_tools(local_store_env):
    with patch.object(sys, "argv", ["objectstore-mcp"]):
        from objectstore_mcp.mcp_server import get_mcp_instance

        mcp, args, _middlewares = get_mcp_instance()
    assert mcp.name == "ObjectStore MCP"
    assert hasattr(args, "transport")


def test_console_script_entry_point():
    from objectstore_mcp.mcp_server import mcp_server

    assert callable(mcp_server)
