"""Action-routed MCP tools over the object-store backends (CONCEPT:OBJ-1.2).

Three consolidated tools — ``objects``, ``buckets``, ``transfer`` — each take
an ``action`` plus a ``params_json`` payload and an optional ``store`` (a
named store from ``OBJECTSTORE_STORES``). The tool layer owns every safety
decision (CONCEPT:OBJ-1.3): size caps, list/batch caps, destructive-operation
flags, dry-run batch deletes, and explicit-bucket requirements for deletes.
Backends stay pure storage adapters.
"""

import base64
import binascii
import json
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from objectstore_mcp.auth import get_backend
from objectstore_mcp.backends.base import ObjectStoreError
from objectstore_mcp.config import Limits, StoreConfig, load_limits, load_stores

_FORBIDDEN_KEY_CHARS = ("*", "?")


def _params(params_json: str) -> dict[str, Any]:
    if not params_json:
        return {}
    parsed = json.loads(params_json)
    if not isinstance(parsed, dict):
        raise ValueError("params_json must decode to a JSON object.")
    return parsed


def _bucket_for(p: dict[str, Any], config: StoreConfig) -> str:
    bucket = p.get("bucket") or config.bucket
    if not bucket:
        raise ValueError(
            f"No bucket given and store {config.name!r} has no default bucket. "
            'Pass {"bucket": "..."} in params_json.'
        )
    return bucket


def _explicit_single_key(p: dict[str, Any], operation: str) -> tuple[str, str]:
    """Deletes target exactly one object: explicit bucket AND key, no wildcards."""
    bucket = p.get("bucket")
    key = p.get("key")
    if not bucket or not key:
        raise ValueError(
            f"{operation} requires an explicit 'bucket' and 'key' in params_json "
            "(store default buckets do not apply to deletes)."
        )
    if any(ch in key for ch in _FORBIDDEN_KEY_CHARS):
        raise ValueError(
            f"{operation} targets exactly one object; wildcard characters are "
            f"not allowed in key {key!r}. Use action='delete_batch' for prefixes."
        )
    return bucket, key

def _decode_payload(p: dict[str, Any], limits: Limits) -> bytes:
    if "text" in p and "content_base64" in p:
        raise ValueError("Provide either 'text' or 'content_base64', not both.")
    if "text" in p:
        data = str(p["text"]).encode("utf-8")
    elif "content_base64" in p:
        try:
            data = base64.b64decode(p["content_base64"], validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError(f"content_base64 is not valid base64: {exc}") from exc
    else:
        raise ValueError("put requires 'text' or 'content_base64' in params_json.")
    if len(data) > limits.max_put_bytes:
        raise ValueError(
            f"Payload is {len(data)} bytes, over the {limits.max_put_bytes}-byte "
            "put cap (OBJECTSTORE_MAX_PUT_BYTES)."
        )
    return data


def _encode_content(data: bytes, mode: str) -> dict[str, Any]:
    if mode not in ("auto", "text", "base64"):
        raise ValueError(f"mode must be 'auto', 'text', or 'base64' (got {mode!r}).")
    if mode in ("auto", "text"):
        try:
            return {"encoding": "text", "content": data.decode("utf-8")}
        except UnicodeDecodeError:
            if mode == "text":
                raise ValueError(
                    "Object is not valid UTF-8 text; use mode='base64'."
                ) from None
    return {"encoding": "base64", "content": base64.b64encode(data).decode("ascii")}


def register_objectstore_tools(mcp: FastMCP) -> None:
    """Register the ``objects``, ``buckets``, and ``transfer`` tools."""

    @mcp.tool(tags={"objects"})
    async def objects(
        action: str = Field(
            description=(
                "Object action. One of: 'list' (prefix/delimiter pagination), "
                "'head' (stat), 'get' (size-capped read; mode text|base64|auto), "
                "'put' (text or content_base64), 'copy', 'move', 'delete' "
                "(explicit bucket+key only), 'delete_batch' (by prefix, capped, "
                "dry-run by default), 'presign' (where the backend supports it), "
                "'metadata_get', 'metadata_set'."
            )
        ),
        params_json: str = Field(
            default="{}",
            description=(
                "JSON of arguments. list: "
                '{"bucket": "b", "prefix": "logs/", "delimiter": "/", '
                '"max_keys": 100, "token": "..."}. head/get/metadata_get: '
                '{"bucket": "b", "key": "k"} (get also takes "mode" and '
                '"max_bytes"). put: {"bucket": "b", "key": "k", "text": "..."} '
                'or {"content_base64": "..."} plus optional "content_type", '
                '"metadata". copy/move: {"bucket": "b", "key": "k", '
                '"dest_bucket": "b2", "dest_key": "k2"}. delete: {"bucket": '
                '"b", "key": "k"} (both required, no wildcards). delete_batch: '
                '{"bucket": "b", "prefix": "tmp/", "max_keys": 50, '
                '"dry_run": true}. presign: {"bucket": "b", "key": "k", '
                '"method": "GET", "expires_in": 3600}. metadata_set: '
                '{"bucket": "b", "key": "k", "metadata": {...}}.'
            ),
        ),
        store: str | None = Field(
            default=None,
            description=(
                "Named store from OBJECTSTORE_STORES (default: the configured "
                "default store; 'local' is always available)."
            ),
        ),
    ) -> Any:
        """List, read, write, copy, move, delete, presign, and tag objects."""
        backend, config = get_backend(store)
        limits = load_limits()
        p = _params(params_json)

        if action == "list":
            bucket = _bucket_for(p, config)
            max_keys = min(int(p.get("max_keys", limits.max_list_keys)), limits.max_list_keys)
            page = backend.list_objects(
                bucket,
                prefix=p.get("prefix", ""),
                delimiter=p.get("delimiter"),
                max_keys=max_keys,
                continuation_token=p.get("token"),
            )
            return {"bucket": bucket, "store": config.name, **page.to_dict()}
        if action == "head":
            bucket = _bucket_for(p, config)
            return backend.head_object(bucket, p["key"]).to_dict()
        if action == "get":
            bucket = _bucket_for(p, config)
            cap = min(int(p.get("max_bytes", limits.max_get_bytes)), limits.max_get_bytes)
            data = backend.get_object(bucket, p["key"], max_bytes=cap)
            return {
                "bucket": bucket,
                "key": p["key"],
                "size": len(data),
                **_encode_content(data, p.get("mode", "auto")),
            }
        if action == "put":
            bucket = _bucket_for(p, config)
            data = _decode_payload(p, limits)
            info = backend.put_object(
                bucket,
                p["key"],
                data,
                content_type=p.get("content_type"),
                metadata=p.get("metadata"),
            )
            return {"bucket": bucket, **info.to_dict()}
        if action in ("copy", "move"):
            bucket = _bucket_for(p, config)
            dest_bucket = p.get("dest_bucket") or bucket
            dest_key = p.get("dest_key")
            if not dest_key:
                raise ValueError(f"{action} requires 'dest_key' in params_json.")
            info = backend.copy_object(bucket, p["key"], dest_bucket, dest_key)
            if action == "move":
                if not limits.allow_object_delete:
                    raise ValueError(
                        "move needs object deletes, which are disabled "
                        "(OBJECTSTORE_ALLOW_DELETE=false)."
                    )
                backend.delete_object(bucket, p["key"])
            return {
                "action": action,
                "source": {"bucket": bucket, "key": p["key"]},
                "dest": {"bucket": dest_bucket, **info.to_dict()},
            }
        if action == "delete":
            if not limits.allow_object_delete:
                raise ValueError(
                    "Object deletes are disabled (OBJECTSTORE_ALLOW_DELETE=false)."
                )
            bucket, key = _explicit_single_key(p, "delete")
            backend.delete_object(bucket, key)
            return {"deleted": True, "bucket": bucket, "key": key}
        if action == "delete_batch":
            if not limits.allow_object_delete:
                raise ValueError(
                    "Object deletes are disabled (OBJECTSTORE_ALLOW_DELETE=false)."
                )
            bucket = p.get("bucket")
            prefix = p.get("prefix")
            if not bucket or not prefix:
                raise ValueError(
                    "delete_batch requires an explicit 'bucket' and a non-empty "
                    "'prefix' (refusing to bulk-delete a whole bucket)."
                )
            max_keys = min(int(p.get("max_keys", limits.max_batch_keys)), limits.max_batch_keys)
            dry_run = bool(p.get("dry_run", True))
            page = backend.list_objects(bucket, prefix=prefix, max_keys=max_keys)
            keys = [obj.key for obj in page.objects]
            if not dry_run:
                for key in keys:
                    backend.delete_object(bucket, key)
            return {
                "bucket": bucket,
                "prefix": prefix,
                "dry_run": dry_run,
                "matched": len(keys),
                "keys": keys,
                "deleted": 0 if dry_run else len(keys),
                "truncated": page.truncated,
            }
        if action == "presign":
            bucket = _bucket_for(p, config)
            url = backend.presigned_url(
                bucket,
                p["key"],
                method=p.get("method", "GET"),
                expires_in=int(p.get("expires_in", 3600)),
            )
            return {"bucket": bucket, "key": p["key"], "url": url}
        if action == "metadata_get":
            bucket = _bucket_for(p, config)
            return {
                "bucket": bucket,
                "key": p["key"],
                "metadata": backend.get_object_metadata(bucket, p["key"]),
            }
        if action == "metadata_set":
            bucket = _bucket_for(p, config)
            info = backend.set_object_metadata(
                bucket, p["key"], p.get("metadata") or {}
            )
            return {"bucket": bucket, **info.to_dict()}
        raise ValueError(f"Unknown objects action: {action!r}.")

    @mcp.tool(tags={"buckets"})
    async def buckets(
        action: str = Field(
            description=(
                "Bucket action. One of: 'list', 'create', 'delete' (empty "
                "buckets only, gated by OBJECTSTORE_ALLOW_BUCKET_DELETE), "
                "'exists', 'info' (location/details), 'stores' (configured "
                "named stores and their backend capabilities)."
            )
        ),
        params_json: str = Field(
            default="{}",
            description=(
                'JSON of arguments, e.g. {"bucket": "b"} for create/delete/'
                'exists/info; create also takes optional "location".'
            ),
        ),
        store: str | None = Field(
            default=None,
            description="Named store from OBJECTSTORE_STORES.",
        ),
    ) -> Any:
        """Manage buckets/containers and inspect configured stores."""
        if action == "stores":
            stores = load_stores()
            return {
                name: {
                    "backend": cfg.backend,
                    "bucket": cfg.bucket,
                    "endpoint": cfg.endpoint,
                }
                for name, cfg in sorted(stores.items())
            }
        backend, config = get_backend(store)
        limits = load_limits()
        p = _params(params_json)

        if action == "list":
            return {
                "store": config.name,
                "buckets": [b.to_dict() for b in backend.list_buckets()],
            }
        if action == "create":
            bucket = _bucket_for(p, config)
            return backend.create_bucket(bucket, location=p.get("location")).to_dict()
        if action == "delete":
            if not limits.allow_bucket_delete:
                raise ValueError(
                    "Bucket deletes are disabled. Set "
                    "OBJECTSTORE_ALLOW_BUCKET_DELETE=true to enable them."
                )
            bucket = p.get("bucket")
            if not bucket:
                raise ValueError(
                    "delete requires an explicit 'bucket' in params_json."
                )
            backend.delete_bucket(bucket)
            return {"deleted": True, "bucket": bucket}
        if action == "exists":
            bucket = _bucket_for(p, config)
            return {"bucket": bucket, "exists": backend.bucket_exists(bucket)}
        if action == "info":
            bucket = _bucket_for(p, config)
            return {
                **backend.bucket_info(bucket).to_dict(),
                "capabilities": backend.capabilities(),
            }
        raise ValueError(f"Unknown buckets action: {action!r}.")

    @mcp.tool(tags={"transfer"})
    async def transfer(
        action: str = Field(
            description=(
                "Transfer action. One of: 'upload' (local file -> object), "
                "'download' (object -> local file), 'upload_dir' (local "
                "directory -> objects under a prefix, capped), "
                "'download_prefix' (objects under a prefix -> local "
                "directory, capped). All transfers are size-capped."
            )
        ),
        params_json: str = Field(
            default="{}",
            description=(
                'JSON of arguments. upload: {"bucket": "b", "local_path": '
                '"/tmp/f.bin", "key": "f.bin", "content_type": "..."}. '
                'download: {"bucket": "b", "key": "k", "local_path": '
                '"/tmp/out.bin", "overwrite": false}. upload_dir: {"bucket": '
                '"b", "local_dir": "/tmp/dir", "prefix": "backup/", '
                '"max_keys": 50}. download_prefix: {"bucket": "b", "prefix": '
                '"backup/", "local_dir": "/tmp/out", "max_keys": 50, '
                '"overwrite": false}.'
            ),
        ),
        store: str | None = Field(
            default=None,
            description="Named store from OBJECTSTORE_STORES.",
        ),
    ) -> Any:
        """Move data between the local filesystem and object storage."""
        backend, config = get_backend(store)
        limits = load_limits()
        p = _params(params_json)

        if action == "upload":
            bucket = _bucket_for(p, config)
            local = Path(p["local_path"]).expanduser()
            if not local.is_file():
                raise ValueError(f"local_path {str(local)!r} is not a file.")
            size = local.stat().st_size
            if size > limits.max_transfer_bytes:
                raise ValueError(
                    f"File is {size} bytes, over the {limits.max_transfer_bytes}-"
                    "byte transfer cap (OBJECTSTORE_MAX_TRANSFER_BYTES)."
                )
            key = p.get("key") or local.name
            info = backend.put_object(
                bucket,
                key,
                local.read_bytes(),
                content_type=p.get("content_type"),
                metadata=p.get("metadata"),
            )
            return {"bucket": bucket, "uploaded": str(local), **info.to_dict()}
        if action == "download":
            bucket = _bucket_for(p, config)
            local = Path(p["local_path"]).expanduser()
            if local.exists() and not p.get("overwrite", False):
                raise ValueError(
                    f"local_path {str(local)!r} exists; pass \"overwrite\": true."
                )
            data = backend.get_object(
                bucket, p["key"], max_bytes=limits.max_transfer_bytes
            )
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(data)
            return {
                "bucket": bucket,
                "key": p["key"],
                "local_path": str(local),
                "size": len(data),
            }
        if action == "upload_dir":
            bucket = _bucket_for(p, config)
            local_dir = Path(p["local_dir"]).expanduser()
            if not local_dir.is_dir():
                raise ValueError(f"local_dir {str(local_dir)!r} is not a directory.")
            prefix = p.get("prefix", "")
            max_keys = min(int(p.get("max_keys", limits.max_batch_keys)), limits.max_batch_keys)
            files = sorted(f for f in local_dir.rglob("*") if f.is_file())
            if len(files) > max_keys:
                raise ValueError(
                    f"Directory holds {len(files)} files, over the {max_keys}-key "
                    "batch cap; raise 'max_keys' (bounded by "
                    "OBJECTSTORE_MAX_BATCH_KEYS) or narrow the directory."
                )
            total = sum(f.stat().st_size for f in files)
            if total > limits.max_transfer_bytes:
                raise ValueError(
                    f"Directory totals {total} bytes, over the "
                    f"{limits.max_transfer_bytes}-byte transfer cap."
                )
            uploaded = []
            for path in files:
                key = prefix + path.relative_to(local_dir).as_posix()
                backend.put_object(bucket, key, path.read_bytes())
                uploaded.append(key)
            return {"bucket": bucket, "uploaded": uploaded, "count": len(uploaded)}
        if action == "download_prefix":
            bucket = _bucket_for(p, config)
            local_dir = Path(p["local_dir"]).expanduser()
            prefix = p.get("prefix", "")
            max_keys = min(int(p.get("max_keys", limits.max_batch_keys)), limits.max_batch_keys)
            overwrite = bool(p.get("overwrite", False))
            page = backend.list_objects(bucket, prefix=prefix, max_keys=max_keys)
            total = sum(obj.size for obj in page.objects)
            if total > limits.max_transfer_bytes:
                raise ValueError(
                    f"Prefix totals {total} bytes, over the "
                    f"{limits.max_transfer_bytes}-byte transfer cap."
                )
            downloaded = []
            for obj in page.objects:
                relative = obj.key[len(prefix):] if prefix else obj.key
                target = local_dir / relative.lstrip("/")
                if target.exists() and not overwrite:
                    raise ValueError(
                        f"{str(target)!r} exists; pass \"overwrite\": true."
                    )
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(
                    backend.get_object(
                        bucket, obj.key, max_bytes=limits.max_transfer_bytes
                    )
                )
                downloaded.append({"key": obj.key, "local_path": str(target)})
            return {
                "bucket": bucket,
                "prefix": prefix,
                "count": len(downloaded),
                "downloaded": downloaded,
                "truncated": page.truncated,
            }
        raise ValueError(f"Unknown transfer action: {action!r}.")

    # Re-exported so linters see the closures as used; FastMCP holds the refs.
    _ = (objects, buckets, transfer)


__all__ = ["register_objectstore_tools", "ObjectStoreError"]
