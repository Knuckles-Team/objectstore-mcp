"""Named-store registry and safety limits (CONCEPT:OBJ-1.1, CONCEPT:OBJ-1.3).

Stores
------
``OBJECTSTORE_STORES`` is a JSON object mapping store names to per-store
settings::

    {
      "media":   {"backend": "s3", "bucket": "media-prod", "profile": "prod"},
      "minio":   {"backend": "s3", "endpoint": "http://minio.arpa:9000"},
      "reports": {"backend": "gcs", "bucket": "acme-reports"},
      "archive": {"backend": "azure", "bucket": "archive"},
      "scratch": {"backend": "filesystem", "root": "~/scratch-store"}
    }

A zero-infra ``local`` filesystem store (rooted at ``OBJECTSTORE_FS_ROOT``,
default ``~/.local/share/objectstore-mcp``) is always present unless the JSON
overrides the name. ``OBJECTSTORE_DEFAULT_STORE`` picks which store tools use
when no ``store`` argument is given (default: first configured store, else
``local``).

Limits
------
Size caps and destructive-operation flags are environment-tunable with sane
defaults; the tool layer enforces them uniformly across all backends.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any

DEFAULT_FS_ROOT = "~/.local/share/objectstore-mcp"
LOCAL_STORE_NAME = "local"

_TRUE = {"1", "true", "yes", "on"}


def _as_bool(raw: str | None, default: bool) -> bool:
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in _TRUE


def _as_int(name: str, raw: str | None, default: int) -> int:
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer (got {raw!r}).") from exc


@dataclass(frozen=True)
class StoreConfig:
    """One named store: a backend plus its connection/default settings."""

    name: str
    backend: str
    bucket: str | None = None
    endpoint: str | None = None
    profile: str | None = None
    region: str | None = None
    root: str | None = None
    project: str | None = None
    connection_string: str | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Limits:
    """Safety caps enforced by the tool layer (CONCEPT:OBJ-1.3)."""

    max_get_bytes: int = 10 * 1024 * 1024
    max_put_bytes: int = 10 * 1024 * 1024
    max_transfer_bytes: int = 100 * 1024 * 1024
    max_batch_keys: int = 100
    max_list_keys: int = 1000
    allow_object_delete: bool = True
    allow_bucket_delete: bool = False


def load_limits() -> Limits:
    """Build the safety limits from the environment."""
    return Limits(
        max_get_bytes=_as_int(
            "OBJECTSTORE_MAX_GET_BYTES",
            os.getenv("OBJECTSTORE_MAX_GET_BYTES"),
            Limits.max_get_bytes,
        ),
        max_put_bytes=_as_int(
            "OBJECTSTORE_MAX_PUT_BYTES",
            os.getenv("OBJECTSTORE_MAX_PUT_BYTES"),
            Limits.max_put_bytes,
        ),
        max_transfer_bytes=_as_int(
            "OBJECTSTORE_MAX_TRANSFER_BYTES",
            os.getenv("OBJECTSTORE_MAX_TRANSFER_BYTES"),
            Limits.max_transfer_bytes,
        ),
        max_batch_keys=_as_int(
            "OBJECTSTORE_MAX_BATCH_KEYS",
            os.getenv("OBJECTSTORE_MAX_BATCH_KEYS"),
            Limits.max_batch_keys,
        ),
        max_list_keys=_as_int(
            "OBJECTSTORE_MAX_LIST_KEYS",
            os.getenv("OBJECTSTORE_MAX_LIST_KEYS"),
            Limits.max_list_keys,
        ),
        allow_object_delete=_as_bool(os.getenv("OBJECTSTORE_ALLOW_DELETE"), True),
        allow_bucket_delete=_as_bool(
            os.getenv("OBJECTSTORE_ALLOW_BUCKET_DELETE"), False
        ),
    )


_KNOWN_FIELDS = {
    "backend",
    "bucket",
    "endpoint",
    "profile",
    "region",
    "root",
    "project",
    "connection_string",
}


def _parse_store(name: str, raw: Any) -> StoreConfig:
    if not isinstance(raw, dict):
        raise ValueError(
            f"OBJECTSTORE_STORES[{name!r}] must be a JSON object (got {raw!r})."
        )
    backend = raw.get("backend")
    if not backend or not isinstance(backend, str):
        raise ValueError(f"OBJECTSTORE_STORES[{name!r}] is missing 'backend'.")
    options = {k: v for k, v in raw.items() if k not in _KNOWN_FIELDS}
    return StoreConfig(
        name=name,
        backend=backend.lower(),
        bucket=raw.get("bucket"),
        endpoint=raw.get("endpoint"),
        profile=raw.get("profile"),
        region=raw.get("region"),
        root=raw.get("root"),
        project=raw.get("project"),
        connection_string=raw.get("connection_string"),
        options=options,
    )


def load_stores() -> dict[str, StoreConfig]:
    """Parse ``OBJECTSTORE_STORES`` and guarantee the ``local`` store exists."""
    raw = os.getenv("OBJECTSTORE_STORES", "").strip()
    stores: dict[str, StoreConfig] = {}
    if raw:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"OBJECTSTORE_STORES is not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("OBJECTSTORE_STORES must be a JSON object.")
        for name, entry in parsed.items():
            stores[name] = _parse_store(name, entry)
    if LOCAL_STORE_NAME not in stores:
        stores[LOCAL_STORE_NAME] = StoreConfig(
            name=LOCAL_STORE_NAME,
            backend="filesystem",
            root=os.getenv("OBJECTSTORE_FS_ROOT", DEFAULT_FS_ROOT),
        )
    return stores


def default_store_name(stores: dict[str, StoreConfig]) -> str:
    """Resolve which store is used when a tool call omits ``store``."""
    explicit = os.getenv("OBJECTSTORE_DEFAULT_STORE", "").strip()
    if explicit:
        if explicit not in stores:
            raise ValueError(
                f"OBJECTSTORE_DEFAULT_STORE={explicit!r} is not a configured "
                f"store (have: {sorted(stores)})."
            )
        return explicit
    for name in stores:
        if name != LOCAL_STORE_NAME:
            return name
    return LOCAL_STORE_NAME
