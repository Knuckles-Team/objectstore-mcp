"""Store resolution and per-backend credential wiring (CONCEPT:OBJ-1.1).

Credentials are never read here directly — each provider SDK resolves its own
chain, and this module only decides *which* store (and therefore which
backend + settings) a tool call targets:

- **S3 / MinIO / R2** — boto3's standard chain (``AWS_ACCESS_KEY_ID``/
  ``AWS_SECRET_ACCESS_KEY`` env, ``~/.aws`` profiles via the store's
  ``profile``, SSO, instance metadata). ``endpoint`` points at MinIO/R2.
- **Google Cloud Storage** — Application Default Credentials
  (``GOOGLE_APPLICATION_CREDENTIALS`` service-account file, gcloud, workload
  identity).
- **Azure Blob** — ``AZURE_STORAGE_CONNECTION_STRING`` (or a per-store
  ``connection_string`` option).
- **Filesystem** — no credentials; a configurable root directory.

Backends are built once per store and cached for the process lifetime.
"""

from objectstore_mcp.api import ObjectStoreBackend, create_backend
from objectstore_mcp.api.api_client_base import ObjectStoreError
from objectstore_mcp.config import StoreConfig, default_store_name, load_stores

_BACKEND_CACHE: dict[str, ObjectStoreBackend] = {}


def resolve_store(store: str | None = None) -> StoreConfig:
    """Resolve a tool call's ``store`` argument to a :class:`StoreConfig`."""
    stores = load_stores()
    name = store or default_store_name(stores)
    config = stores.get(name)
    if config is None:
        raise ObjectStoreError(
            f"Unknown store {name!r}. Configured stores: {sorted(stores)}."
        )
    return config


def get_backend(store: str | None = None) -> tuple[ObjectStoreBackend, StoreConfig]:
    """Return the (cached) backend and config for a named store."""
    config = resolve_store(store)
    backend = _BACKEND_CACHE.get(config.name)
    if backend is None:
        backend = create_backend(config)
        _BACKEND_CACHE[config.name] = backend
    return backend, config


def reset_backend_cache() -> None:
    """Drop cached backends (tests and config reloads)."""
    _BACKEND_CACHE.clear()


def get_client(store: str | None = None) -> ObjectStoreBackend:
    """Golden ``get_client()`` entry point: backend for a named store.

    Wraps any resolution/credential failure in
    ``RuntimeError("AUTHENTICATION ERROR: ...")`` per the connector standard.
    """
    try:
        backend, _config = get_backend(store)
    except Exception as exc:
        raise RuntimeError(f"AUTHENTICATION ERROR: {exc}") from exc
    return backend
