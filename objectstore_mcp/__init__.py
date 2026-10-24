"""objectstore-mcp — multi-backend object-storage API + MCP Server + A2A Agent.

One MCP tool surface (objects/buckets/transfer) over S3 and S3-compatible
stores (MinIO, Cloudflare R2), Google Cloud Storage, Azure Blob Storage, and
a zero-infra local-filesystem backend (CONCEPT:OB-OS.governance.every-provider-implements-same).
"""

from agent_connector_sdk.connector import Connector

from objectstore_mcp.api import ObjectStoreBackend
from objectstore_mcp.auth import get_client

connector = Connector(
    api=ObjectStoreBackend,
    get_client=get_client,
    tools="objectstore_mcp.mcp_server",
    instructions="Object-storage MCP server - one tool surface over S3 and S3-compatible stores (MinIO/R2), Google Cloud Storage, Azure Blob, and a zero-infra local-filesystem backend. Tools: 'objects' (list/head/get/put/copy/move/delete/presign/metadata), 'buckets' (list/create/delete/exists/info/stores), 'transfer' (upload/download, single or by prefix). Named stores come from OBJECTSTORE_STORES; the 'local' filesystem store always exists.",
)

__all__ = ["connector"]
