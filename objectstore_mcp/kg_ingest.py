"""Native epistemic-graph ingestion for object-store metadata.

Object bytes remain in their authoritative backing store; only store, bucket, object,
and storage metadata is materialized.

All writes use the ``agent_connector_sdk.ingest`` knowledge-ingest facade. Nodes use
canonical ``node_type`` and edges use canonical ``relationship``; nodes and edges commit
in one epistemic-graph transaction. Missing engine configuration, rejected records,
checkpoint conflicts, and transaction failures propagate as ``IngestError`` (or a
subclass).
"""

from __future__ import annotations

import logging
from typing import Any

from agent_connector_sdk.ingest import (
    ChangeSet,
    Entity,
    IngestBinding,
    IngestError,
    KnowledgeIngest,
    Relationship,
    current_ingest,
)

logger = logging.getLogger("objectstore_mcp.kg")

_SOURCE = "objectstore-mcp"
_DOMAIN = "objectstore"

_BINDING = IngestBinding(connector=_SOURCE, stream=_DOMAIN)


def _to_entity(record: dict[str, Any]) -> Entity:
    return Entity(
        id=record.get("id"),
        node_type=record.get("node_type"),
        properties={
            k: v for k, v in record.items() if k not in ("id", "node_type")
        },
    )


def _to_relationship(record: dict[str, Any]) -> Relationship:
    props = {
        k: v
        for k, v in record.items()
        if k not in ("source", "target", "relationship")
    }
    return Relationship(
        source=record["source"],
        target=record["target"],
        relationship=record["relationship"],
        properties=props or None,
    )


async def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    ingest: KnowledgeIngest | None = None,
) -> dict[str, int]:
    """Write canonical typed nodes and relationships in one epistemic-graph commit."""
    if not entities:
        raise IngestError("ingest_entities needs at least one entity")
    change_set = ChangeSet(
        entities=tuple(_to_entity(e) for e in entities),
        relationships=tuple(_to_relationship(r) for r in relationships or ()),
    )
    service = ingest or current_ingest()
    receipt = await service.submit(_BINDING, change_set)
    return {"nodes": receipt.affected_count, "edges": receipt.relationship_count}


def _store_id(store: str) -> str:
    return f"objectstore:store:{store}"


def _bucket_id(store: str, bucket: str) -> str:
    return f"objectstore:bucket:{store}/{bucket}"


def _object_id(store: str, bucket: str, key: str) -> str:
    return f"objectstore:object:{store}/{bucket}/{key}"


def _store_entity(
    store: str, backend: str | None, endpoint: str | None
) -> dict[str, Any]:
    return {
        "id": _store_id(store),
        "node_type": "ObjectStore",
        "name": store,
        "backendType": backend,
        "endpoint": endpoint,
        "externalToolId": store,
    }


async def ingest_buckets(
    buckets: list[dict[str, Any]],
    *,
    store: str,
    backend: str | None = None,
    endpoint: str | None = None,
    ingest: KnowledgeIngest | None = None,
) -> dict[str, int]:
    """Map bucket records → ``:Bucket`` (+ owning ``:ObjectStore``) nodes and ingest.

    ``buckets``: dicts shaped like ``BucketInfo.to_dict()`` (``name``/``created``/
    ``location``). ``store`` is the configured store name they belong to.
    """
    entities: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    seen_store = False
    for b in buckets or []:
        name = b.get("name")
        if not name:
            continue
        if not seen_store:
            entities.append(_store_entity(store, backend, endpoint))
            seen_store = True
        bid = _bucket_id(store, name)
        entities.append(
            {
                "id": bid,
                "node_type": "Bucket",
                "name": name,
                "created": b.get("created"),
                "location": b.get("location"),
                "backendType": backend,
                "externalToolId": f"{store}/{name}",
            }
        )
        relationships.append(
            {"source": bid, "target": _store_id(store), "relationship": "inStore"}
        )
    return await ingest_entities(entities, relationships, ingest=ingest)


async def ingest_objects(
    objects: list[dict[str, Any]],
    *,
    store: str,
    bucket: str,
    ingest: KnowledgeIngest | None = None,
) -> dict[str, int]:
    """Map object records → ``:Object`` nodes under a ``:Bucket`` and ingest.

    ``objects``: dicts shaped like ``ObjectInfo.to_dict()`` (``key``/``size``/``etag``/
    ``content_type``/``last_modified``/``storage_class``). Object metadata only — the
    raw bytes are never copied into the graph.
    """
    entities: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    bid = _bucket_id(store, bucket)
    seen_bucket = False
    for o in objects or []:
        key = o.get("key")
        if not key:
            continue
        if not seen_bucket:
            entities.append(
                {
                    "id": bid,
                    "node_type": "Bucket",
                    "name": bucket,
                    "externalToolId": f"{store}/{bucket}",
                }
            )
            seen_bucket = True
        oid = _object_id(store, bucket, key)
        entities.append(
            {
                "id": oid,
                "node_type": "Object",
                "name": key,
                "objectKey": key,
                "byteSize": o.get("size"),
                "etag": o.get("etag"),
                "contentType": o.get("content_type"),
                "lastModified": o.get("last_modified"),
                "storageClass": o.get("storage_class"),
                "externalToolId": f"{store}/{bucket}/{key}",
            }
        )
        relationships.append({"source": oid, "target": bid, "relationship": "inBucket"})
    return await ingest_entities(entities, relationships, ingest=ingest)


__all__ = ["ingest_entities", "ingest_buckets", "ingest_objects"]
