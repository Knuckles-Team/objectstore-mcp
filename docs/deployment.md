# Deployment

<!-- BEGIN GENERATED: deployment-options -->
## Deployment Options

`objectstore-mcp` supports local stdio, a loopback-only development listener, a
least-privilege stdio container, and a remote authenticated HTTPS boundary.
Provider endpoint, credential, selector, identity, and trust material are supplied
at runtime through `AgentConfig`; none is stored in this repository.

### Installed stdio process

```json
{
  "mcpServers": {
    "objectstore": {
      "command": "objectstore-mcp",
      "args": [],
      "env": {"MCP_TOOL_MODE": "intent"}
    }
  }
}
```

### Loopback development listener

```bash
objectstore-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

Do not expose this listener beyond loopback. Network deployments require direct TLS
or an explicitly trusted TLS-terminating ingress, configured authentication, exact
`MCP_ALLOWED_HOSTS`, and an exact trusted-proxy CIDR policy.

### Least-privilege local container

```bash
docker run -i --rm \
  --read-only \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --pids-limit=256 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  -e TRANSPORT=stdio \
  registry.example.invalid/objectstore-mcp@sha256:<digest> objectstore-mcp
```

The operator projects the selected AgentConfig profile into the process at runtime;
the image remains immutable and contains no environment connection profile.

### Remote authenticated HTTPS endpoint

```json
{
  "mcpServers": {
    "objectstore": {"url": "https://service.example.invalid/mcp"}
  }
}
```

Store the real remote URL, outbound identity reference, and TLS-profile reference in
`AgentConfig`, not in MCP client JSON or documentation.
<!-- END GENERATED: deployment-options -->

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
