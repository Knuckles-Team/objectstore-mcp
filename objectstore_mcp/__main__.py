"""Module entry point: ``python -m objectstore_mcp`` runs the MCP server."""

from objectstore_mcp.mcp_server import mcp_server

if __name__ == "__main__":
    mcp_server()
