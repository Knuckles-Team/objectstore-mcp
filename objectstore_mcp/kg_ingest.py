"""Native epistemic-graph ingestion for object-store metadata.

Object bytes remain in their authoritative backing store; only store, bucket, object,
and storage metadata is materialized.

All writes use the required ``agent_utilities.knowledge_graph.memory.native_ingest``
primitive. Nodes use canonical ``node_type`` and edges use canonical ``relationship``;
nodes and edges commit in one native transaction. Missing engine dependencies, rejected
records, conflicts, and transaction failures propagate as ``NativeIngestError``.
"""

from __future__ import annotations

import logging
from typing import Any

from agent_utilities.knowledge_graph.memory.native_ingest import (
    ingest_entities as _native_ingest_entities,
)

logger = logging.getLogger("objectstore_mcp.kg")

_SOURCE = "objectstore-mcp"
_DOMAIN = "objectstore"


def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Write canonical typed nodes and relationships in one native transaction."""
    return _native_ingest_entities(
        entities,
        relationships,
        source=source,
        domain=domain,
        client=client,
        graph=graph,
    )


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


def ingest_buckets(
    buckets: list[dict[str, Any]],
    *,
    store: str,
    backend: str | None = None,
    endpoint: str | None = None,
    client: Any | None = None,
    graph: str | None = None,
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
    return ingest_entities(entities, relationships, client=client, graph=graph)


def ingest_objects(
    objects: list[dict[str, Any]],
    *,
    store: str,
    bucket: str,
    client: Any | None = None,
    graph: str | None = None,
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
    return ingest_entities(entities, relationships, client=client, graph=graph)


__all__ = ["ingest_entities", "ingest_buckets", "ingest_objects"]
