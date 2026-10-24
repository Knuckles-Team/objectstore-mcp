"""Main FastMCP server and tool registration for objectstore-mcp."""

from objectstore_mcp.mcp.mcp_objectstore import register_objectstore_tools  # noqa: F401

# SDK discovery registers the register_<tag>_tools functions bound in this module.
__all__ = ["register_objectstore_tools"]
