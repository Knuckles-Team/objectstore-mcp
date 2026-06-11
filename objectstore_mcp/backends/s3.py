"""Amazon S3 / S3-compatible backend (CONCEPT:OBJ-1.5).

Covers AWS S3 plus any S3-compatible endpoint (MinIO, Cloudflare R2, Ceph RGW)
via the ``endpoint`` store option. Credentials resolve through boto3's own
chain (env vars, shared config/credentials files, SSO, instance metadata);
``profile`` selects a named profile from that chain.

Requires the ``s3`` extra: ``pip install objectstore-mcp[s3]``.
"""

from typing import Any

from objectstore_mcp.backends.base import (
    AlreadyExistsError,
    BucketInfo,
    BucketNotEmptyError,
    Metadata,
    MissingDependencyError,
    NotFoundError,
    ObjectInfo,
    ObjectPage,
    ObjectStoreError,
    validate_bucket_name,
    validate_key,
)

_NOT_FOUND_CODES = {"404", "NoSuchKey", "NoSuchBucket", "NotFound"}


def _build_client(
    endpoint: str | None, profile: str | None, region: str | None
) -> Any:
    try:
        import boto3
    except ImportError as exc:  # pragma: no cover - exercised via mocked import
        raise MissingDependencyError(
            "The S3 backend requires boto3. Install it with "
            "`pip install objectstore-mcp[s3]`."
        ) from exc
    session = boto3.session.Session(profile_name=profile, region_name=region)
    return session.client("s3", endpoint_url=endpoint)


class S3Backend:
    """S3 and S3-compatible (MinIO/R2) object-store backend."""

    backend_type = "s3"

    def __init__(
        self,
        endpoint: str | None = None,
        profile: str | None = None,
        region: str | None = None,
        client: Any | None = None,
    ):
        """``client`` injects a pre-built boto3 S3 client (used by tests)."""
        self.client = client if client is not None else _build_client(
            endpoint, profile, region
        )

    def capabilities(self) -> dict[str, bool]:
        return {
            "presigned_urls": True,
            "object_metadata": True,
            "bucket_location": True,
        }

    # -- error translation ---------------------------------------------------
    def _translate(self, exc: Exception, context: str) -> ObjectStoreError:
        code = ""
        response = getattr(exc, "response", None)
        if isinstance(response, dict):
            code = str(response.get("Error", {}).get("Code", ""))
        if code in _NOT_FOUND_CODES:
            return NotFoundError(f"{context} not found.")
        if code in ("BucketAlreadyExists", "BucketAlreadyOwnedByYou"):
            return AlreadyExistsError(f"{context} already exists.")
        if code == "BucketNotEmpty":
            return BucketNotEmptyError(f"{context} is not empty.")
        return ObjectStoreError(f"{context}: {exc}")

    # -- buckets -------------------------------------------------------------
    def list_buckets(self) -> list[BucketInfo]:
        try:
            response = self.client.list_buckets()
        except Exception as exc:
            raise self._translate(exc, "Bucket listing") from exc
        buckets = []
        for entry in response.get("Buckets", []):
            created = entry.get("CreationDate")
            buckets.append(
                BucketInfo(
                    name=entry["Name"],
                    created=created.isoformat() if created else None,
                )
            )
        return buckets

    def create_bucket(self, bucket: str, location: str | None = None) -> BucketInfo:
        validate_bucket_name(bucket)
        kwargs: dict[str, Any] = {"Bucket": bucket}
        if location and location != "us-east-1":
            kwargs["CreateBucketConfiguration"] = {"LocationConstraint": location}
        try:
            self.client.create_bucket(**kwargs)
        except Exception as exc:
            raise self._translate(exc, f"Bucket {bucket!r}") from exc
        return BucketInfo(name=bucket, location=location)

    def delete_bucket(self, bucket: str) -> None:
        try:
            self.client.delete_bucket(Bucket=bucket)
        except Exception as exc:
            raise self._translate(exc, f"Bucket {bucket!r}") from exc

    def bucket_exists(self, bucket: str) -> bool:
        try:
            self.client.head_bucket(Bucket=bucket)
            return True
        except Exception as exc:
            translated = self._translate(exc, f"Bucket {bucket!r}")
            if isinstance(translated, NotFoundError):
                return False
            raise translated from exc

    def bucket_info(self, bucket: str) -> BucketInfo:
        try:
            response = self.client.get_bucket_location(Bucket=bucket)
        except Exception as exc:
            raise self._translate(exc, f"Bucket {bucket!r}") from exc
        return BucketInfo(
            name=bucket, location=response.get("LocationConstraint") or "us-east-1"
        )

    # -- objects ---------------------------------------------------------------
    def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        delimiter: str | None = None,
        max_keys: int = 1000,
        continuation_token: str | None = None,
    ) -> ObjectPage:
        kwargs: dict[str, Any] = {
            "Bucket": bucket,
            "Prefix": prefix,
            "MaxKeys": max_keys,
        }
        if delimiter:
            kwargs["Delimiter"] = delimiter
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token
        try:
            response = self.client.list_objects_v2(**kwargs)
        except Exception as exc:
            raise self._translate(exc, f"Bucket {bucket!r}") from exc
        page = ObjectPage(
            next_token=response.get("NextContinuationToken"),
            truncated=bool(response.get("IsTruncated", False)),
            prefixes=[p["Prefix"] for p in response.get("CommonPrefixes", [])],
        )
        for entry in response.get("Contents", []):
            modified = entry.get("LastModified")
            page.objects.append(
                ObjectInfo(
                    key=entry["Key"],
                    size=entry.get("Size", 0),
                    etag=(entry.get("ETag") or "").strip('"') or None,
                    last_modified=modified.isoformat() if modified else None,
                    storage_class=entry.get("StorageClass"),
                )
            )
        return page

    def head_object(self, bucket: str, key: str) -> ObjectInfo:
        try:
            response = self.client.head_object(Bucket=bucket, Key=key)
        except Exception as exc:
            raise self._translate(exc, f"Object {bucket!r}/{key!r}") from exc
        modified = response.get("LastModified")
        return ObjectInfo(
            key=key,
            size=response.get("ContentLength", 0),
            etag=(response.get("ETag") or "").strip('"') or None,
            last_modified=modified.isoformat() if modified else None,
            content_type=response.get("ContentType"),
            metadata=dict(response.get("Metadata") or {}),
            storage_class=response.get("StorageClass"),
        )

    def get_object(self, bucket: str, key: str, max_bytes: int | None = None) -> bytes:
        info = self.head_object(bucket, key)
        if max_bytes is not None and info.size > max_bytes:
            raise ObjectStoreError(
                f"Object {bucket!r}/{key!r} is {info.size} bytes, over the "
                f"{max_bytes}-byte read cap."
            )
        try:
            response = self.client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except Exception as exc:
            raise self._translate(exc, f"Object {bucket!r}/{key!r}") from exc

    def put_object(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str | None = None,
        metadata: Metadata | None = None,
    ) -> ObjectInfo:
        validate_key(key)
        kwargs: dict[str, Any] = {"Bucket": bucket, "Key": key, "Body": data}
        if content_type:
            kwargs["ContentType"] = content_type
        if metadata:
            kwargs["Metadata"] = dict(metadata)
        try:
            response = self.client.put_object(**kwargs)
        except Exception as exc:
            raise self._translate(exc, f"Object {bucket!r}/{key!r}") from exc
        return ObjectInfo(
            key=key,
            size=len(data),
            etag=(response.get("ETag") or "").strip('"') or None,
            content_type=content_type,
            metadata=dict(metadata or {}),
        )

    def copy_object(
        self, src_bucket: str, src_key: str, dst_bucket: str, dst_key: str
    ) -> ObjectInfo:
        validate_key(dst_key)
        try:
            self.client.copy_object(
                Bucket=dst_bucket,
                Key=dst_key,
                CopySource={"Bucket": src_bucket, "Key": src_key},
            )
        except Exception as exc:
            raise self._translate(
                exc, f"Copy {src_bucket!r}/{src_key!r} -> {dst_bucket!r}/{dst_key!r}"
            ) from exc
        return self.head_object(dst_bucket, dst_key)

    def delete_object(self, bucket: str, key: str) -> None:
        # S3 deletes are idempotent and return 204 for missing keys; check
        # first so callers get a consistent NotFoundError across backends.
        self.head_object(bucket, key)
        try:
            self.client.delete_object(Bucket=bucket, Key=key)
        except Exception as exc:
            raise self._translate(exc, f"Object {bucket!r}/{key!r}") from exc

    def get_object_metadata(self, bucket: str, key: str) -> dict[str, str]:
        return self.head_object(bucket, key).metadata

    def set_object_metadata(
        self, bucket: str, key: str, metadata: Metadata
    ) -> ObjectInfo:
        info = self.head_object(bucket, key)
        kwargs: dict[str, Any] = {
            "Bucket": bucket,
            "Key": key,
            "CopySource": {"Bucket": bucket, "Key": key},
            "Metadata": dict(metadata or {}),
            "MetadataDirective": "REPLACE",
        }
        if info.content_type:
            kwargs["ContentType"] = info.content_type
        try:
            self.client.copy_object(**kwargs)
        except Exception as exc:
            raise self._translate(exc, f"Object {bucket!r}/{key!r}") from exc
        return self.head_object(bucket, key)

    def presigned_url(
        self, bucket: str, key: str, method: str = "GET", expires_in: int = 3600
    ) -> str:
        operations = {"GET": "get_object", "PUT": "put_object"}
        operation = operations.get(method.upper())
        if operation is None:
            raise ObjectStoreError(
                f"Presign method must be GET or PUT (got {method!r})."
            )
        try:
            return self.client.generate_presigned_url(
                operation,
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        except Exception as exc:
            raise self._translate(exc, f"Presign {bucket!r}/{key!r}") from exc
