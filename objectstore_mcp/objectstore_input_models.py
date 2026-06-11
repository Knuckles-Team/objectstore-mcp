#!/usr/bin/python
"""Pydantic input models for objectstore-mcp tool parameters (CONCEPT:OBJ-1.2).

Typed contracts for the ``params_json`` payloads accepted by the three
action-routed MCP tools (``objects``, ``buckets``, ``transfer``).
"""

from pydantic import BaseModel, Field


class ObjectKeyInput(BaseModel):
    """Input model for single-object actions (head/get/delete/metadata/presign)."""

    bucket: str = Field(description="Bucket/container name (always explicit).")
    key: str = Field(description="Object key.")


class ObjectPutInput(BaseModel):
    """Input model for the ``objects`` 'put' action."""

    bucket: str = Field(description="Bucket/container name.")
    key: str = Field(description="Object key to write.")
    content: str = Field(description="Inline content (text, or base64 when binary).")
    content_type: str | None = Field(
        default=None, description="MIME type stored with the object."
    )
    encoding: str | None = Field(
        default=None, description="'text' (default) or 'base64'."
    )


class ObjectListInput(BaseModel):
    """Input model for the ``objects`` 'list' action."""

    bucket: str = Field(description="Bucket/container name.")
    prefix: str | None = Field(default=None, description="Key prefix filter.")
    max_keys: int | None = Field(
        default=None, description="Page size (clamped to the server list cap)."
    )
    continuation_token: str | None = Field(
        default=None, description="Opaque token from the previous page."
    )


class ObjectCopyInput(BaseModel):
    """Input model for the ``objects`` 'copy' / 'move' actions."""

    bucket: str = Field(description="Source bucket.")
    key: str = Field(description="Source key.")
    dest_bucket: str = Field(description="Destination bucket.")
    dest_key: str = Field(description="Destination key.")


class TransferInput(BaseModel):
    """Input model for the ``transfer`` tool (upload/download)."""

    bucket: str = Field(description="Bucket/container name.")
    key: str | None = Field(
        default=None, description="Single object key (omit when using prefix)."
    )
    prefix: str | None = Field(
        default=None, description="Key prefix for bulk transfer."
    )
    path: str = Field(description="Local filesystem path (file or directory).")
