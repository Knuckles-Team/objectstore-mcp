"""Public client facade for objectstore_mcp (backward-compatible re-export)."""

from objectstore_mcp.api import (
    BACKEND_ALIASES,
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
    create_backend,
)

__all__ = [
    "BACKEND_ALIASES",
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
]
