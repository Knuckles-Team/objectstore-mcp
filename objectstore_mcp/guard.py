"""The safety governor every tool call goes through (CONN-OBJECTSTORE-MCP-R006).

CONCEPT:OB-OS.safety.size-caps-list-batch. The SDK generates one tool per
``ObjectStoreBackend`` method and calls the backend that ``get_client`` returns,
so the caps and destructive-operation flags are enforced here, on a wrapper
around that backend, instead of in each tool. Backends stay pure storage
adapters; the wrapper changes no result, it only refuses.
"""

from typing import Any

from scion_sdk.storage import ObjectInfo, ObjectPage

from objectstore_mcp.config import load_limits

_FORBIDDEN_KEY_CHARS = ("*", "?")


class GuardedBackend:
    """An ``ObjectStoreBackend`` that applies the environment's ``Limits``."""

    def __init__(self, backend: Any) -> None:
        # A backend that is already guarded is not wrapped twice.
        self._backend = (
            backend.inner if isinstance(backend, GuardedBackend) else backend
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._backend, name)

    @property
    def inner(self) -> Any:
        """The wrapped SDK backend."""
        return self._backend

    def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        delimiter: str | None = None,
        max_keys: int | None = None,
        continuation_token: str | None = None,
    ) -> ObjectPage:
        cap = load_limits().max_list_keys
        return self._backend.list_objects(
            bucket,
            prefix=prefix,
            delimiter=delimiter,
            max_keys=min(max_keys or cap, cap),
            continuation_token=continuation_token,
        )

    def get_object(self, bucket: str, key: str, max_bytes: int | None = None) -> bytes:
        cap = load_limits().max_get_bytes
        return self._backend.get_object(
            bucket, key, max_bytes=min(cap if max_bytes is None else max_bytes, cap)
        )

    def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes | str,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> ObjectInfo:
        payload = data.encode("utf-8") if isinstance(data, str) else data
        cap = load_limits().max_put_bytes
        if len(payload) > cap:
            raise ValueError(
                f"Payload is {len(payload)} bytes, over the {cap}-byte put cap "
                "(OBJECTSTORE_MAX_PUT_BYTES); use objectstore_upload_file."
            )
        return self._backend.put_object(
            bucket, key, payload, content_type=content_type, metadata=metadata
        )

    def delete_object(self, bucket: str, key: str) -> None:
        if not load_limits().allow_object_delete:
            raise ValueError(
                "Object deletes are disabled (OBJECTSTORE_ALLOW_DELETE=false)."
            )
        if not bucket or not key:
            raise ValueError("delete requires an explicit bucket and key.")
        if any(ch in key for ch in _FORBIDDEN_KEY_CHARS):
            raise ValueError(
                f"delete targets exactly one object; wildcard characters are not "
                f"allowed in key {key!r}. Use objectstore_delete_objects_by_prefix."
            )
        self._backend.delete_object(bucket, key)

    def delete_bucket(self, bucket: str) -> None:
        if not load_limits().allow_bucket_delete:
            raise ValueError(
                "Bucket deletes are disabled. Set OBJECTSTORE_ALLOW_BUCKET_DELETE=true "
                "to enable them."
            )
        self._backend.delete_bucket(bucket)


__all__ = ["GuardedBackend"]
