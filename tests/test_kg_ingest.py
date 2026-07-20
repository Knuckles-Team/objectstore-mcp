"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``ingest_entities`` / ``ingest_buckets`` / ``ingest_objects`` seam
with a fake engine client (no engine required), asserting the txn add_node/commit +
edge calls and the object-store record → :ObjectStore/:Bucket/:Object mapping.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

import pytest
from agent_utilities.knowledge_graph.memory.native_ingest import NativeIngestError

from objectstore_mcp.kg_ingest import ingest_buckets, ingest_entities, ingest_objects


class _FakeTxn:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.committed = False

    def begin(self, graph=None):
        self.graph = graph
        return "txn-1"

    def add_node(self, txn, node_id, props):
        self.nodes[node_id] = props

    def add_edge(self, txn, source, target, props):
        self.edges.append((source, target, props))

    def commit(self, txn):
        self.committed = True
        return True


class _FakeClient:
    def __init__(self):
        self.txn = _FakeTxn()


def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
        [
            {"id": "a", "node_type": "Bucket", "name": "b"},
            {"id": "s", "node_type": "ObjectStore"},
        ],
        [{"source": "a", "target": "s", "relationship": "inStore"}],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 2, "edges": 1}
    assert c.txn.committed is True
    assert set(c.txn.nodes) == {"a", "s"}
    # provenance is stamped
    assert c.txn.nodes["a"]["source"] == "objectstore-mcp"
    assert c.txn.nodes["a"]["domain"] == "objectstore"
    assert c.txn.edges == [("a", "s", {"relationship": "inStore"})]


def test_ingest_buckets_maps_bucket_and_store():
    c = _FakeClient()
    res = ingest_buckets(
        [
            {"name": "media-prod", "created": "2026-01-01T00:00:00Z", "location": "us"},
            {"name": "reports"},
        ],
        store="minio",
        backend="s3",
        endpoint="http://minio.example:9000",
        client=c,
        graph="__commons__",
    )
    # 1 store node + 2 bucket nodes; 2 inStore edges
    assert res == {"nodes": 3, "edges": 2}
    store_node = c.txn.nodes["objectstore:store:minio"]
    assert store_node["node_type"] == "ObjectStore"
    assert store_node["backendType"] == "s3"
    assert store_node["endpoint"] == "http://minio.example:9000"
    bucket_node = c.txn.nodes["objectstore:bucket:minio/media-prod"]
    assert bucket_node["node_type"] == "Bucket"
    assert bucket_node["location"] == "us"
    assert bucket_node["externalToolId"] == "minio/media-prod"
    assert (
        "objectstore:bucket:minio/media-prod",
        "objectstore:store:minio",
        {"relationship": "inStore"},
    ) in c.txn.edges


def test_ingest_objects_maps_object_and_bucket():
    c = _FakeClient()
    res = ingest_objects(
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
        client=c,
        graph="__commons__",
    )
    # 1 bucket node + 1 object node; 1 inBucket edge
    assert res == {"nodes": 2, "edges": 1}
    obj = c.txn.nodes["objectstore:object:local/scratch/logs/app.log"]
    assert obj["node_type"] == "Object"
    assert obj["objectKey"] == "logs/app.log"
    assert obj["byteSize"] == 1234
    assert obj["contentType"] == "text/plain"
    assert obj["storageClass"] == "STANDARD"
    assert c.txn.nodes["objectstore:bucket:local/scratch"]["node_type"] == "Bucket"
    assert c.txn.edges == [
        (
            "objectstore:object:local/scratch/logs/app.log",
            "objectstore:bucket:local/scratch",
            {"relationship": "inBucket"},
        )
    ]


def test_retired_structural_alias_is_rejected():
    with pytest.raises(NativeIngestError, match="canonical node_type"):
        ingest_entities([{"id": "a", "type": "Bucket"}], client=_FakeClient())


def test_empty_native_ingest_is_rejected():
    with pytest.raises(NativeIngestError, match="at least one entity"):
        ingest_entities([], client=_FakeClient())
