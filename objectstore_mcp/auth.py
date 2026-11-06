"""Store resolution (CONN-OBJECTSTORE-MCP-R001).

This module decides *which* store a tool call targets. The SDK builds the
backend (``scion_sdk.storage.create_backend``) and resolves the store's
credential references; no ambient provider credential chain is consulted.
Backends are built once per store and cached for the process lifetime.
"""

from scion_sdk.storage import StorageError, create_backend

from objectstore_mcp.config import StoreConfig, default_store_name, load_stores
from objectstore_mcp.guard import GuardedBackend

_BACKEND_CACHE: dict[str, GuardedBackend] = {}


def entitled_store_names(names: list[str]) -> list[str]:
    """Filter a store-name list to what the calling identity may reach.

    Routes the names through ``scion_sdk.entitlements``' identity-scoped
    resolver: a bound actor's roles/groups decide which named object stores
    auto-load for them, and an unauthenticated or tenant-less bound actor fails
    closed (``PermissionError``). When no actor is bound at all (local stdio use)
    every configured store is visible, as before.
    """
    from scion_sdk.entitlements import identity_scoped_resources
    from scion_sdk.identity import IdentityRequiredError, current_actor

    try:
        actor = current_actor()
    except IdentityRequiredError:
        return list(names)
    return list(identity_scoped_resources("objectstore", names, actor=actor))


def resolve_store(store: str | None = None) -> StoreConfig:
    """Resolve a tool call's ``store`` argument to a :class:`StoreConfig`.

    Resolved against the caller's identity entitlements: an omitted ``store``
    auto-selects the caller's entitled default, and a named store they are not
    entitled to is denied.
    """
    stores = load_stores()
    entitled = entitled_store_names(list(stores))
    if not store:
        default = default_store_name(stores)
        if default in entitled:
            return stores[default]
        if entitled:
            return stores[entitled[0]]
        raise StorageError(
            "No object stores are available to your identity. Your "
            "Okta/Keycloak groups grant none of the configured stores."
        )
    config = stores.get(store)
    if config is None:
        raise StorageError(
            f"Unknown store {store!r}. Configured stores: {sorted(stores)}."
        )
    if store not in entitled:
        raise PermissionError(
            f"Your identity is not entitled to the object store {store!r}. "
            f"Entitled: {', '.join(entitled) or '(none)'}"
        )
    return config


def get_backend(store: str | None = None) -> tuple[GuardedBackend, StoreConfig]:
    """Return the (cached) backend for a named store, behind the safety governor."""
    config = resolve_store(store)
    backend = _BACKEND_CACHE.get(config.name)
    if backend is None:
        backend = GuardedBackend(create_backend(config))
        _BACKEND_CACHE[config.name] = backend
    return backend, config


def reset_backend_cache() -> None:
    """Drop cached backends (tests and config reloads)."""
    _BACKEND_CACHE.clear()


def get_client(store: str | None = None) -> GuardedBackend:
    """Golden ``get_client()`` entry point: backend for a named store.

    Wraps any resolution/credential failure in
    ``RuntimeError("AUTHENTICATION ERROR: ...")`` per the connector standard.
    The refusal keeps the cause: the SDK storage error's ``code`` and message
    (which never carry a credential), so an egress refusal, a missing provider
    library or an entitlement denial reads as itself (CONN-OBJECTSTORE-MCP-R005).
    """
    try:
        backend, _config = get_backend(store)
    except StorageError as exc:
        raise RuntimeError(f"AUTHENTICATION ERROR: {exc.code}: {exc}") from exc
    except PermissionError as exc:
        raise RuntimeError(f"AUTHENTICATION ERROR: not entitled: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"AUTHENTICATION ERROR: {type(exc).__name__}") from exc
    return backend
