# objectstore-mcp

The object-storage connector for the agent-utilities fleet: one MCP tool
surface (`objects` / `buckets` / `transfer`) over S3 and S3-compatible stores
(MinIO, Cloudflare R2), Google Cloud Storage, Azure Blob Storage, and a
zero-infra local-filesystem backend.

- [Installation](installation.md)
- [Usage](usage.md)
- [Architecture](architecture.md)
- [Concept registry](concepts.md)

## Why one connector

Agents need durable blob storage for artifacts, datasets, backups, and
hand-offs between tools. Instead of one MCP server per provider, this
connector multiplexes named stores (`OBJECTSTORE_STORES`) across providers
behind a single, safety-governed tool surface — and because the filesystem
backend implements the same protocol, everything works on a laptop with no
cloud credentials.
