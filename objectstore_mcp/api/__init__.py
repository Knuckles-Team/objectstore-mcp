"""Object-store backends come from the SDK (CONN-OBJECTSTORE-MCP-R001).

The connector ships no backend: every store is built by
:func:`scion_sdk.storage.create_backend` (SCION-CENTRALIZED-CAPABILITIES-R042).
This module re-exports the SDK names the tool layer uses.
"""

from scion_sdk.storage import (
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
    StorageError,
    StoreConfig,
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
    "StorageError",
    "StoreConfig",
    "UnsupportedOperationError",
    "create_backend",
]
