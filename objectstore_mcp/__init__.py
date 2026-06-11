"""objectstore-mcp — multi-backend object-storage MCP connector.

One MCP tool surface (objects/buckets/transfer) over S3 and S3-compatible
stores (MinIO, Cloudflare R2), Google Cloud Storage, Azure Blob Storage, and
a zero-infra local-filesystem backend (CONCEPT:OBJ-1.0).
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
