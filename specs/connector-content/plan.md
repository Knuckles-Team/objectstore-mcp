# CONN-OBJECTSTORE-MCP-CONNECTOR-CONTENT — Design and implementation plan

Governing spec: [spec.md](spec.md).

## Architecture

`pyproject.toml` declares `objectstore-mcp` as the connector identity. `create_mcp_server` resolves the packaged content of `objectstore_mcp` from it.
