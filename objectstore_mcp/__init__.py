"""objectstore-mcp — multi-backend object-storage API + MCP Server + A2A Agent.

One typed MCP tool surface over S3 and S3-compatible
stores (MinIO, Cloudflare R2), Google Cloud Storage, Azure Blob Storage, and
a zero-infra local-filesystem backend (CONCEPT:OB-OS.governance.every-provider-implements-same).
"""

from scion_sdk.connector import Connector

from objectstore_mcp.api import ObjectStoreBackend
from objectstore_mcp.auth import get_client

connector = Connector(
    api=ObjectStoreBackend,
    get_client=get_client,
    tools="objectstore_mcp.mcp_server",
    instructions="Object-storage MCP server: the durable asset store. One typed tool per operation over S3 and S3-compatible stores, Google Cloud Storage, Azure Blob, WebDAV and a local filesystem store. Buckets and objects: objectstore_list_buckets/create_bucket/delete_bucket/bucket_info, objectstore_list_objects/head_object/get_object/put_object/copy_object/delete_object, objectstore_presigned_url, metadata get/set. Guarded composites: objectstore_move_object, objectstore_delete_objects_by_prefix (dry run first), file and directory transfers. S3 management: lifecycle rules, versioning, object tags. objectstore_list_stores names the stores your identity may reach.",
)

__all__ = ["connector"]
