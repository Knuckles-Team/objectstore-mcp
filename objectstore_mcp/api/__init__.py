"""Backend factory: map a store's ``backend`` string to an implementation.

Imports are lazy so the core install carries zero cloud dependencies
(CONCEPT:OBJ-1.5); a missing SDK surfaces as :class:`MissingDependencyError`
naming the pip extra to install.
"""

import os

from objectstore_mcp.api.api_client_base import (
    AlreadyExistsError,
    BucketInfo,
    BucketNotEmptyError,
    InvalidNameError,
    Metadata,
    MissingDependencyError,
    NotFoundError,
    ObjectInfo,
    ObjectPage,
    ObjectStoreBackend,
    ObjectStoreError,
    UnsupportedOperationError,
)
from objectstore_mcp.config import DEFAULT_FS_ROOT, StoreConfig

__all__ = [
    "AlreadyExistsError",
    "BucketInfo",
    "BucketNotEmptyError",
    "InvalidNameError",
    "Metadata",
    "MissingDependencyError",
    "NotFoundError",
    "ObjectInfo",
    "ObjectPage",
    "ObjectStoreBackend",
    "ObjectStoreError",
    "UnsupportedOperationError",
    "create_backend",
    "BACKEND_ALIASES",
]

BACKEND_ALIASES = {
    "filesystem": "filesystem",
    "fs": "filesystem",
    "local": "filesystem",
    "s3": "s3",
    "minio": "s3",
    "r2": "s3",
    "gcs": "gcs",
    "gcp": "gcs",
    "google": "gcs",
    "azure": "azure",
    "azure_blob": "azure",
    "abs": "azure",
}


def create_backend(store: StoreConfig) -> ObjectStoreBackend:
    """Instantiate the backend a :class:`StoreConfig` names."""
    kind = BACKEND_ALIASES.get(store.backend)
    if kind == "filesystem":
        from objectstore_mcp.api.api_client_filesystem import FilesystemBackend

        root = store.root or os.getenv("OBJECTSTORE_FS_ROOT") or DEFAULT_FS_ROOT
        return FilesystemBackend(root=root)
    if kind == "s3":
        from objectstore_mcp.api.api_client_s3 import S3Backend

        return S3Backend(
            endpoint=store.endpoint, profile=store.profile, region=store.region
        )
    if kind == "gcs":
        from objectstore_mcp.api.api_client_gcs import GCSBackend

        return GCSBackend(project=store.project)
    if kind == "azure":
        from objectstore_mcp.api.api_client_azure_blob import AzureBlobBackend

        return AzureBlobBackend(connection_string=store.connection_string)
    raise ObjectStoreError(
        f"Unknown backend {store.backend!r} for store {store.name!r}. "
        f"Valid backends: {sorted(set(BACKEND_ALIASES))}."
    )
