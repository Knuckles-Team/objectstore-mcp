#!/usr/bin/python
# coding: utf-8
"""Pydantic response models for objectstore-mcp payloads (CONCEPT:OBJ-1.2).

Typed contracts mirroring the dataclass envelopes returned by the
:mod:`objectstore_mcp.api` backends and surfaced through the MCP tools.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ObjectInfoResponse(BaseModel):
    """One object's listing/HEAD envelope."""

    bucket: Optional[str] = Field(default=None, description="Bucket/container name.")
    key: Optional[str] = Field(default=None, description="Object key.")
    size: Optional[int] = Field(default=None, description="Object size in bytes.")
    etag: Optional[str] = Field(default=None, description="Entity tag / hash.")
    last_modified: Optional[str] = Field(
        default=None, description="Last-modified timestamp (ISO-8601)."
    )
    content_type: Optional[str] = Field(default=None, description="MIME type.")
    metadata: Optional[dict[str, Any]] = Field(
        default=None, description="User metadata key/values."
    )


class ObjectPageResponse(BaseModel):
    """One page of an object listing."""

    objects: Optional[list[ObjectInfoResponse]] = Field(
        default=None, description="Objects on this page."
    )
    continuation_token: Optional[str] = Field(
        default=None, description="Token for the next page (None when exhausted)."
    )
    truncated: Optional[bool] = Field(
        default=None, description="True when more pages remain."
    )


class BucketInfoResponse(BaseModel):
    """One bucket/container envelope."""

    name: Optional[str] = Field(default=None, description="Bucket/container name.")
    created: Optional[str] = Field(
        default=None, description="Creation timestamp (ISO-8601), where available."
    )
    raw: Optional[dict[str, Any]] = Field(
        default=None, description="Raw provider payload."
    )
