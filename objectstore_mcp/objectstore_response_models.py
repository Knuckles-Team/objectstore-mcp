#!/usr/bin/python
"""Pydantic response models for objectstore-mcp payloads (CONCEPT:OBJ-1.2).

Typed contracts mirroring the dataclass envelopes returned by the
:mod:`objectstore_mcp.api` backends and surfaced through the MCP tools.
"""

from typing import Any

from pydantic import BaseModel, Field


class ObjectInfoResponse(BaseModel):
    """One object's listing/HEAD envelope."""

    bucket: str | None = Field(default=None, description="Bucket/container name.")
    key: str | None = Field(default=None, description="Object key.")
    size: int | None = Field(default=None, description="Object size in bytes.")
    etag: str | None = Field(default=None, description="Entity tag / hash.")
    last_modified: str | None = Field(
        default=None, description="Last-modified timestamp (ISO-8601)."
    )
    content_type: str | None = Field(default=None, description="MIME type.")
    metadata: dict[str, Any] | None = Field(
        default=None, description="User metadata key/values."
    )


class ObjectPageResponse(BaseModel):
    """One page of an object listing."""

    objects: list[ObjectInfoResponse] | None = Field(
        default=None, description="Objects on this page."
    )
    continuation_token: str | None = Field(
        default=None, description="Token for the next page (None when exhausted)."
    )
    truncated: bool | None = Field(
        default=None, description="True when more pages remain."
    )


class BucketInfoResponse(BaseModel):
    """One bucket/container envelope."""

    name: str | None = Field(default=None, description="Bucket/container name.")
    created: str | None = Field(
        default=None, description="Creation timestamp (ISO-8601), where available."
    )
    raw: dict[str, Any] | None = Field(
        default=None, description="Raw provider payload."
    )
