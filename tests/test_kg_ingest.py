"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``ingest_entities`` / ``ingest_buckets`` / ``ingest_objects`` seam
against a fake transport boundary (one level below ``KnowledgeIngest``), so the SDK's
own request-building and validation contract runs unmodified. Asserts the object-store
record → :ObjectStore/:Bucket/:Object mapping lands as real
``SourceRecord``/``SourceRelationship`` objects.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from agent_connector_sdk.ingest import IngestError, KnowledgeIngest

from objectstore_mcp.kg_ingest import ingest_buckets, ingest_entities, ingest_objects


class _FakeTransport:
    def __init__(self) -> None:
        self.requests: list[Any] = []

    async def source_status(self, connector: str, stream: str) -> Any:
        return SimpleNamespace(accepted_checkpoint=None)

    async def submit(self, request: Any) -> Any:
        self.requests.append(request)
        return SimpleNamespace(
            affected_count=len(request.records),
            relationship_count=len(request.relationships),
        )

    async def store_blob(self, data: bytes) -> str:
        raise AssertionError("this connector's ingestion carries no media")


@pytest.fixture
def ingest() -> tuple[KnowledgeIngest, _FakeTransport]:
    transport = _FakeTransport()
    return KnowledgeIngest(transport, loop=None), transport


@pytest.mark.asyncio
async def test_ingest_entities_writes_nodes_and_edges(ingest):
    service, transport = ingest
    res = await ingest_entities(
        [
            {"id": "a", "node_type": "Bucket", "name": "b"},
            {"id": "s", "node_type": "ObjectStore"},
        ],
        [{"source": "a", "target": "s", "relationship": "inStore"}],
        ingest=service,
    )
    assert res == {"nodes": 2, "edges": 1}
    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert {r.record_id for r in request.records} == {"a", "s"}
    bucket_record = next(r for r in request.records if r.record_id == "a")
    assert bucket_record.mapping_reference.endswith("schema_mappings/Bucket")
    assert bucket_record.payload["name"] == "b"
    rel = request.relationships[0]
    assert rel.source.record_id == "a"
    assert rel.target.record_id == "s"
    assert rel.relation_reference.endswith("/relations/inStore")


@pytest.mark.asyncio
async def test_ingest_buckets_maps_bucket_and_store(ingest):
    service, transport = ingest
    res = await ingest_buckets(
        [
            {"name": "media-prod", "created": "2026-01-01T00:00:00Z", "location": "us"},
            {"name": "reports"},
        ],
        store="minio",
        backend="s3",
        endpoint="http://minio.example:9000",
        ingest=service,
    )
    # 1 store node + 2 bucket nodes; 2 inStore edges
    assert res == {"nodes": 3, "edges": 2}
    request = transport.requests[0]
    records = {r.record_id: r for r in request.records}
    store_record = records["objectstore:store:minio"]
    assert store_record.mapping_reference.endswith("schema_mappings/ObjectStore")
    assert store_record.payload["backendType"] == "s3"
    bucket_record = records["objectstore:bucket:minio/media-prod"]
    assert bucket_record.mapping_reference.endswith("schema_mappings/Bucket")
    assert bucket_record.payload["location"] == "us"
    assert bucket_record.payload["externalToolId"] == "minio/media-prod"
    assert (
        "objectstore:bucket:minio/media-prod",
        "objectstore:store:minio",
    ) in {(r.source.record_id, r.target.record_id) for r in request.relationships}
    assert all(
        r.relation_reference.endswith("/relations/inStore")
        for r in request.relationships
    )


@pytest.mark.asyncio
async def test_ingest_objects_maps_object_and_bucket(ingest):
    service, transport = ingest
    res = await ingest_objects(
        [
            {
                "key": "logs/app.log",
                "size": 1234,
                "etag": "abc",
                "content_type": "text/plain",
                "last_modified": "2026-02-02T00:00:00Z",
                "storage_class": "STANDARD",
            }
        ],
        store="local",
        bucket="scratch",
        ingest=service,
    )
    # 1 bucket node + 1 object node; 1 inBucket edge
    assert res == {"nodes": 2, "edges": 1}
    request = transport.requests[0]
    records = {r.record_id: r for r in request.records}
    obj = records["objectstore:object:local/scratch/logs/app.log"]
    assert obj.mapping_reference.endswith("schema_mappings/Object")
    assert obj.payload["objectKey"] == "logs/app.log"
    assert obj.payload["byteSize"] == 1234
    assert obj.payload["contentType"] == "text/plain"
    assert obj.payload["storageClass"] == "STANDARD"
    assert records["objectstore:bucket:local/scratch"].mapping_reference.endswith(
        "schema_mappings/Bucket"
    )
    assert len(request.relationships) == 1
    rel = request.relationships[0]
    assert rel.source.record_id == "objectstore:object:local/scratch/logs/app.log"
    assert rel.target.record_id == "objectstore:bucket:local/scratch"
    assert rel.relation_reference.endswith("/relations/inBucket")


@pytest.mark.asyncio
async def test_retired_structural_alias_is_rejected(ingest):
    service, _transport = ingest
    with pytest.raises(IngestError, match="id and a node_type"):
        await ingest_entities([{"id": "a", "type": "Bucket"}], ingest=service)


@pytest.mark.asyncio
async def test_empty_native_ingest_is_rejected(ingest):
    service, _transport = ingest
    with pytest.raises(IngestError, match="at least one entity"):
        await ingest_entities([], ingest=service)
