"""Native epistemic-graph ingestion for object-store metadata (typed graph nodes).

CONCEPT:AU-KG.ingest.enterprise-source-extractor. The objectstore-mcp package natively
pushes its data into the ONE epistemic-graph knowledge graph as **typed OWL nodes**
(:ObjectStore, :Bucket, :Object) + links (:inStore, :inBucket), using the lightweight
engine client (``GraphComputeEngine()._client`` + ``txn``) — the same fast client the
blob ``MediaStore`` uses, NOT the heavy in-process ingestion engine.

Object storage IS itself a blob backend, so this mapper models object **metadata only**
(key, size, etag, content-type, storage-class) and deliberately does NOT copy object
bytes into the graph — the bytes stay in the backing store. The nodes match the classes
federated by ``objectstore_mcp.ontology`` (``objectstore.ttl``).

Everything is dependency-/engine-guarded: with no agent-utilities KG stack or no reachable
engine, every entry point **no-ops** (returns ``None``), so the connector keeps working with
zero KG infrastructure. When the shared ``agent_utilities`` native-ingest primitive is present
it is used directly; otherwise a self-contained txn fallback writes the same nodes/edges.
Node ids follow ``objectstore:<class>:<externalId>``.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("objectstore_mcp.kg")

_SOURCE = "objectstore-mcp"
_DOMAIN = "objectstore"
_DEFAULT_GRAPH = "__commons__"

# Prefer the shared fleet primitive when the installed agent_utilities ships it.
try:  # pragma: no cover - exercised only where the primitive is installed
    from agent_utilities.knowledge_graph.memory.native_ingest import (
        ingest_entities as _shared_ingest_entities,
    )
except Exception:  # noqa: BLE001 — primitive not yet in installed agent_utilities
    _shared_ingest_entities = None


def _client() -> tuple[Any | None, str]:
    """Return ``(engine_client, graph_name)`` or ``(None, "")`` when unavailable."""
    try:
        from agent_utilities.knowledge_graph.core.graph_compute import (
            GraphComputeEngine,
        )
    except Exception as e:  # noqa: BLE001 — KG stack absent
        logger.debug("KG ingest unavailable (import): %s", e)
        return None, ""
    try:
        engine = GraphComputeEngine()
        client = getattr(engine, "_client", None)
        if client is None:
            return None, ""
        graph = getattr(engine, "graph_name", None) or _DEFAULT_GRAPH
        return client, graph
    except Exception as e:  # noqa: BLE001 — engine unreachable
        logger.debug("KG ingest: engine unreachable: %s", e)
        return None, ""


def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Write typed nodes (+ edges) into epistemic-graph via the fast engine client.

    ``entities``: ``[{"id":..., "type":<owl:Class>, ...props}]``.
    ``relationships``: ``[{"source":id, "target":id, "type":rel}]``.
    Returns ``{"nodes":n, "edges":m}`` or ``None`` (no engine / failure; never raises).
    ``client``/``graph`` may be injected (tests); otherwise resolved on demand.
    """
    entities = [e for e in (entities or []) if e.get("id")]
    if not entities:
        return None
    # No injected client: delegate to the shared primitive when it is installed.
    if client is None and _shared_ingest_entities is not None:
        return _shared_ingest_entities(
            entities, relationships, source=source, domain=domain
        )
    if client is None:
        client, graph = _client()
    if client is None:
        return None
    graph = graph or _DEFAULT_GRAPH

    try:
        txn = client.txn.begin(graph=graph)
        for ent in entities:
            props = {k: v for k, v in ent.items() if k != "id" and v is not None}
            props.setdefault("source", source)
            props.setdefault("domain", domain)
            client.txn.add_node(txn, ent["id"], props)
        committed = client.txn.commit(txn)
    except Exception as e:  # noqa: BLE001 — engine/txn failure is non-fatal
        logger.warning("KG ingest: txn failed: %s", e)
        return None
    if not committed:
        logger.warning("KG ingest: txn not committed (conflict)")
        return None

    edges = 0
    for rel in relationships or []:
        try:
            client.edges.add(
                rel["source"], rel["target"], {"type": rel.get("type", "RELATED")}
            )
            edges += 1
        except Exception as e:  # noqa: BLE001 — pure edge link, best-effort
            logger.debug("KG ingest: edge skipped: %s", e)

    logger.info("KG ingest: wrote %d nodes, %d edges", len(entities), edges)
    return {"nodes": len(entities), "edges": edges}


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
        "type": "ObjectStore",
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
) -> dict[str, int] | None:
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
                "type": "Bucket",
                "name": name,
                "created": b.get("created"),
                "location": b.get("location"),
                "backendType": backend,
                "externalToolId": f"{store}/{name}",
            }
        )
        relationships.append(
            {"source": bid, "target": _store_id(store), "type": "inStore"}
        )
    return ingest_entities(entities, relationships, client=client, graph=graph)


def ingest_objects(
    objects: list[dict[str, Any]],
    *,
    store: str,
    bucket: str,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
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
                    "type": "Bucket",
                    "name": bucket,
                    "externalToolId": f"{store}/{bucket}",
                }
            )
            seen_bucket = True
        oid = _object_id(store, bucket, key)
        entities.append(
            {
                "id": oid,
                "type": "Object",
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
        relationships.append({"source": oid, "target": bid, "type": "inBucket"})
    return ingest_entities(entities, relationships, client=client, graph=graph)


__all__ = ["ingest_entities", "ingest_buckets", "ingest_objects"]
