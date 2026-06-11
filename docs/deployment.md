# Deployment

This page covers running `objectstore-mcp` as long-lived servers.

> `objectstore-mcp` ships both an **MCP server** (console script
> `objectstore-mcp`) and an **A2A agent server** (console script
> `objectstore-agent`).

## Run the MCP server

=== "stdio (default)"

    ```bash
    objectstore-mcp
    ```

=== "streamable-http"

    ```bash
    objectstore-mcp --transport streamable-http --host 0.0.0.0 --port 8000
    ```

=== "sse"

    ```bash
    objectstore-mcp --transport sse --host 0.0.0.0 --port 8000
    ```

Health check (HTTP transports):

```bash
curl -s http://localhost:8000/health        # {"status":"OK"}
```

## Docker Compose

```bash
docker compose -f docker/mcp.compose.yml up -d      # MCP server only
docker compose -f docker/agent.compose.yml up -d    # MCP + agent
```

Stores, limits, and toggles come from `../.env` (see
[`.env.example`](https://github.com/Knuckles-Team/objectstore-mcp/blob/main/.env.example)).

## Run the A2A agent server

```bash
objectstore-agent --mcp-config mcp_config.json --web
```

## Ingress & DNS

Behind the fleet's Caddy reverse proxy, publish the streamable-http MCP
endpoint and register the hostname in Technitium DNS; point clients at
`https://objectstore-mcp.<zone>/mcp`.
