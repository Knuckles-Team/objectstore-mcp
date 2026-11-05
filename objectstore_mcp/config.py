"""Named-store registry and safety limits (CONCEPT:OB-OS.config.obj, CONCEPT:OB-OS.safety.size-caps-list-batch).

Stores
------
``OBJECTSTORE_STORES`` is a JSON object mapping store names to per-store
settings, parsed by the SDK store registry (SCION-CENTRALIZED-CAPABILITIES-R042.6).
Secrets are references only::

    {
      "media":   {"backend": "s3", "endpoint": "https://objects.example", "bucket": "media",
                  "credentials": {"access_key_id": "env://MEDIA_KEY_ID",
                                  "secret_access_key": "openbao://kv/media#secret"}},
      "share":   {"backend": "webdav", "endpoint": "https://files.example/dav/files/svc",
                  "credentials": {"username": "env://SHARE_USER", "password": "env://SHARE_PASS"}},
      "scratch": {"backend": "filesystem", "root": "/srv/scratch-store"}
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
from dataclasses import dataclass

from scion_sdk.storage import StoreConfig, parse_stores

__all__ = [
    "DEFAULT_FS_ROOT",
    "LOCAL_STORE_NAME",
    "Limits",
    "StoreConfig",
    "default_store_name",
    "load_limits",
    "load_stores",
]

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
class Limits:
    """Safety caps enforced by the tool layer (CONCEPT:OB-OS.safety.size-caps-list-batch)."""

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


def load_stores() -> dict[str, StoreConfig]:
    """Parse ``OBJECTSTORE_STORES`` and guarantee the ``local`` store exists."""
    raw = os.getenv("OBJECTSTORE_STORES", "").strip()
    stores: dict[str, StoreConfig] = {}
    if raw:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"OBJECTSTORE_STORES is not valid JSON: {type(exc).__name__}"
            ) from exc
        if not isinstance(parsed, dict):
            raise ValueError("OBJECTSTORE_STORES must be a JSON object.")
        stores.update(parse_stores(parsed))
    if LOCAL_STORE_NAME not in stores:
        root = os.path.expanduser(os.getenv("OBJECTSTORE_FS_ROOT", DEFAULT_FS_ROOT))
        stores[LOCAL_STORE_NAME] = StoreConfig(
            name=LOCAL_STORE_NAME, backend="filesystem", root=root
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
