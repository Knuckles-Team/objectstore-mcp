# ObjectStore MCP
## Multi-Backend Object Storage | MCP Server

![PyPI - Version](https://img.shields.io/pypi/v/objectstore-mcp)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
![PyPI - License](https://img.shields.io/pypi/l/objectstore-mcp)

The object-storage connector for the agent-utilities fleet: **one MCP tool
surface over S3 and S3-compatible stores (MinIO, Cloudflare R2), Google Cloud
Storage, Azure Blob Storage, and a zero-infra local-filesystem backend**.

*Version: 0.3.0*

> **Documentation** — Installation, deployment, and usage across the API, CLI, and
> MCP interfaces are maintained in [`docs/`](docs/index.md).

## Table of Contents

- [Overview](#overview)
- [What it provides](#what-it-provides)
- [Backend × capability matrix](#backend--capability-matrix)
- [Installation](#installation)
- [Configuration (environment)](#configuration-environment)
- [Usage](#usage)
- [MCP config](#mcp-config)
- [Docker deployment](#docker-deployment)
- [Development](#development)
- [License](#license)

## Overview

`objectstore-mcp` wraps heterogeneous object stores behind one typed,
deterministic MCP tool surface, plus an optional Pydantic-AI A2A agent server
(`objectstore-agent`). Safety caps, explicit buckets, and dry-run-by-default
batch deletes are enforced uniformly in the tool layer, regardless of backend.

## What it provides

- **A multi-backend store abstraction** (`objectstore_mcp.api`,
  CONCEPT:OBJ-1.0) — every provider implements the same
  `ObjectStoreBackend` protocol, validated by a single conformance test
  suite that runs for real against the filesystem backend.
- **Three consolidated, action-routed MCP tools** (`objectstore-mcp`
  console script):

  | Tool | Actions | Description |
  |---|---|---|
  | `objects` | `list` (prefix/delimiter pagination), `head`, `get` (text/base64, size-capped), `put` (text/base64, size-capped), `copy`, `move`, `delete`, `delete_batch` (capped, dry-run by default), `presign`, `metadata_get`, `metadata_set` | Single-object lifecycle and listing on any store |
  | `buckets` | `list`, `create`, `delete` (empty-only, opt-in), `exists`, `info`, `stores` | Bucket/container admin and store registry introspection |
  | `transfer` | `upload`, `download`, `upload_dir`, `download_prefix` (all size/batch-capped) | Local-filesystem ⇄ object-store transfer, single or by prefix |

  The whole tool set toggles with `OBJECTSTORETOOL`.

- **Named multi-store routing** — `OBJECTSTORE_STORES` JSON maps store names
  to `{backend, bucket?, endpoint?, profile?, ...}`; every tool takes an
  optional `store` argument. A zero-infra `local` filesystem store always
  exists, so the server works with no cloud credentials at all.
- **A safety governor** — size caps on get/put/transfer, list/batch key caps,
  deletes that demand an explicit bucket+key (no wildcards), batch deletes
  that are prefix-scoped, capped, and dry-run by default, and bucket deletes
  that are empty-only and disabled unless explicitly enabled.

## Backend × capability matrix

| Capability | filesystem | s3 / minio / r2 | gcs | azure |
|---|---|---|---|---|
| buckets (list/create/delete/exists/info) | yes | yes | yes | yes |
| objects (list/head/get/put/copy/move/delete) | yes | yes | yes | yes |
| prefix + delimiter listing, pagination | yes | yes | yes | yes |
| user metadata get/set | yes | yes | yes | yes |
| presigned URLs | no | yes | yes (needs service-account key) | yes (needs account key) |
| bucket location | no | yes | yes | no |

## Installation

```bash
pip install objectstore-mcp            # core: local filesystem backend only
pip install objectstore-mcp[s3]        # + boto3 (S3, MinIO, R2)
pip install objectstore-mcp[gcs]       # + google-cloud-storage
pip install objectstore-mcp[azure]     # + azure-storage-blob
pip install objectstore-mcp[all]       # everything (incl. MCP + agent extras)
```

Or pull the container image:

```bash
docker pull knucklessg1/objectstore-mcp:latest
```

## Configuration (environment)

| Var | Default | Meaning |
|---|---|---|
| `OBJECTSTORE_STORES` | _(empty)_ | JSON: store name → `{backend, bucket?, endpoint?, profile?, region?, root?, project?, connection_string?}` |
| `OBJECTSTORE_DEFAULT_STORE` | first configured store, else `local` | Store used when a tool call omits `store` |
| `OBJECTSTORE_FS_ROOT` | `~/.local/share/objectstore-mcp` | Root of the implicit `local` filesystem store |
| `OBJECTSTORE_MAX_GET_BYTES` | `10485760` (10 MiB) | Cap on `objects get` |
| `OBJECTSTORE_MAX_PUT_BYTES` | `10485760` (10 MiB) | Cap on `objects put` |
| `OBJECTSTORE_MAX_TRANSFER_BYTES` | `104857600` (100 MiB) | Cap per transfer (single or batch total) |
| `OBJECTSTORE_MAX_BATCH_KEYS` | `100` | Cap on batch delete / dir transfer key counts |
| `OBJECTSTORE_MAX_LIST_KEYS` | `1000` | Cap on one listing page |
| `OBJECTSTORE_ALLOW_DELETE` | `true` | Object deletes (delete/delete_batch/move) |
| `OBJECTSTORE_ALLOW_BUCKET_DELETE` | `false` | Bucket deletes (empty buckets only) |
| `OBJECTSTORETOOL` | `True` | Register the objectstore tool set |
| `HOST` / `PORT` / `TRANSPORT` | `0.0.0.0` / `8000` / `stdio` | MCP server bind + transport (`stdio`, `streamable-http`, `sse`) |
| `AUTH_TYPE` | `none` | MCP auth mode (container image) |
| `ENABLE_OTEL` | `True` | OTEL/Langfuse telemetry export |
| `EUNOMIA_TYPE` / `EUNOMIA_POLICY_FILE` | `none` / `mcp_policies.json` | Eunomia access-governance middleware |
| `DEFAULT_AGENT_NAME` / `AGENT_DESCRIPTION` / `AGENT_SYSTEM_PROMPT` | identity defaults | A2A agent server identity overrides |
| `MCP_URL` | _(empty)_ | MCP endpoint the A2A agent connects to |

Provider credentials resolve through each SDK's own chain — boto3's
resolution order for S3 (env keys, `~/.aws` profiles via the store's
`profile`, SSO, instance metadata), `GOOGLE_APPLICATION_CREDENTIALS` /
Application Default Credentials for GCS, and
`AZURE_STORAGE_CONNECTION_STRING` for Azure Blob.

### Example store registry

```json
{
  "media":   {"backend": "s3", "bucket": "media-prod", "profile": "prod", "region": "us-east-1"},
  "minio":   {"backend": "s3", "endpoint": "http://minio.arpa:9000"},
  "r2":      {"backend": "s3", "endpoint": "https://<account>.r2.cloudflarestorage.com"},
  "reports": {"backend": "gcs", "bucket": "acme-reports"},
  "archive": {"backend": "azure", "bucket": "archive"},
  "scratch": {"backend": "filesystem", "root": "~/scratch-store"}
}
```

## Usage

```bash
objectstore-mcp                                   # stdio
objectstore-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

Example tool calls (any MCP client):

```jsonc
// Write then read a text object on the zero-infra local store
{"tool": "buckets",  "arguments": {"action": "create", "params_json": "{\"bucket\": \"notes\"}"}}
{"tool": "objects",  "arguments": {"action": "put",    "params_json": "{\"bucket\": \"notes\", \"key\": \"todo.md\", \"text\": \"- ship it\"}"}}
{"tool": "objects",  "arguments": {"action": "get",    "params_json": "{\"bucket\": \"notes\", \"key\": \"todo.md\"}"}}

// Preview then execute a prefix-scoped batch delete on a named S3 store
{"tool": "objects", "arguments": {"store": "media", "action": "delete_batch", "params_json": "{\"bucket\": \"media-prod\", \"prefix\": \"tmp/\"}"}}
{"tool": "objects", "arguments": {"store": "media", "action": "delete_batch", "params_json": "{\"bucket\": \"media-prod\", \"prefix\": \"tmp/\", \"dry_run\": false}"}}
```

## MCP config

```json
{
  "mcpServers": {
    "objectstore-mcp": {
      "command": "uv",
      "args": ["run", "objectstore-mcp"],
      "env": {
        "OBJECTSTORE_STORES": "{\"minio\": {\"backend\": \"s3\", \"endpoint\": \"http://minio.arpa:9000\"}}",
        "OBJECTSTORE_DEFAULT_STORE": "local"
      }
    }
  }
}
```

Run the A2A agent server against a live MCP server:

```bash
objectstore-agent --mcp-url http://localhost:8000/mcp --host 0.0.0.0 --port 9001
```

<!-- BEGIN GENERATED: additional-deployment-options -->
### Additional Deployment Options

`objectstore-mcp` can also run as a **local container** (Docker / Podman / `uv`) or be
consumed from a **remote deployment**. The
[Deployment guide](https://knuckles-team.github.io/objectstore-mcp/deployment/) has full, copy-paste
`mcp_config.json` for all four transports — **stdio**, **streamable-http**,
**local container / uv**, and **remote URL**:

- **Local container / uv** — launch the server from `mcp_config.json` via `uvx`,
  `docker run`, or `podman run`, or point at a local streamable-http container by `url`.
- **Remote URL** — connect to a server deployed behind Caddy at
  `http://objectstore-mcp.arpa/mcp` using the `"url"` key.
<!-- END GENERATED: additional-deployment-options -->

## Docker deployment

```bash
docker compose -f docker/mcp.compose.yml up -d      # MCP server only
docker compose -f docker/agent.compose.yml up -d    # MCP + A2A agent
curl -s http://localhost:8000/health                 # {"status":"OK"}
```

Both services read configuration from `../.env` (copy
[`.env.example`](.env.example)); see [`docs/deployment.md`](docs/deployment.md).

## Development

```bash
pip install -e .[test]
pytest                       # full suite (cloud SDKs not required)
pip install -e .[test-s3]    # adds boto3+moto integration tests
pre-commit run --all-files
```

See [`docs/`](docs/) for architecture, concepts, and deployment details.

## License

MIT — see [LICENSE](LICENSE).
