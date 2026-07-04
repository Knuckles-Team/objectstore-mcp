"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``ingest_entities`` / ``ingest_buckets`` / ``ingest_objects`` seam
with a fake engine client (no engine required), asserting the txn add_node/commit +
edge calls and the object-store record → :ObjectStore/:Bucket/:Object mapping.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

import objectstore_mcp.kg_ingest as kg
from objectstore_mcp.kg_ingest import ingest_buckets, ingest_entities, ingest_objects


class _FakeTxn:
    def __init__(self):
        self.nodes = {}
        self.committed = False

    def begin(self, graph=None):
        self.graph = graph
        return "txn-1"

    def add_node(self, txn, node_id, props):
        self.nodes[node_id] = props

    def commit(self, txn):
        self.committed = True
        return True


class _FakeEdges:
    def __init__(self):
        self.edges = []

    def add(self, src, dst, props):
        self.edges.append((src, dst, props))


class _FakeClient:
    def __init__(self):
        self.txn = _FakeTxn()
        self.edges = _FakeEdges()


def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
        [
            {"id": "a", "type": "Bucket", "name": "b"},
            {"id": "s", "type": "ObjectStore"},
        ],
        [{"source": "a", "target": "s", "type": "inStore"}],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 2, "edges": 1}
    assert c.txn.committed is True
    assert set(c.txn.nodes) == {"a", "s"}
    # provenance is stamped
    assert c.txn.nodes["a"]["source"] == "objectstore-mcp"
    assert c.txn.nodes["a"]["domain"] == "objectstore"
    assert c.edges.edges == [("a", "s", {"type": "inStore"})]


def test_ingest_buckets_maps_bucket_and_store():
    c = _FakeClient()
    res = ingest_buckets(
        [
            {"name": "media-prod", "created": "2026-01-01T00:00:00Z", "location": "us"},
            {"name": "reports"},
        ],
        store="minio",
        backend="s3",
        endpoint="http://minio.arpa:9000",
        client=c,
        graph="__commons__",
    )
    # 1 store node + 2 bucket nodes; 2 inStore edges
    assert res == {"nodes": 3, "edges": 2}
    store_node = c.txn.nodes["objectstore:store:minio"]
    assert store_node["type"] == "ObjectStore"
    assert store_node["backendType"] == "s3"
    assert store_node["endpoint"] == "http://minio.arpa:9000"
    bucket_node = c.txn.nodes["objectstore:bucket:minio/media-prod"]
    assert bucket_node["type"] == "Bucket"
    assert bucket_node["location"] == "us"
    assert bucket_node["externalToolId"] == "minio/media-prod"
    assert (
        "objectstore:bucket:minio/media-prod",
        "objectstore:store:minio",
        {"type": "inStore"},
    ) in c.edges.edges


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
    assert obj["type"] == "Object"
    assert obj["objectKey"] == "logs/app.log"
    assert obj["byteSize"] == 1234
    assert obj["contentType"] == "text/plain"
    assert obj["storageClass"] == "STANDARD"
    assert c.txn.nodes["objectstore:bucket:local/scratch"]["type"] == "Bucket"
    assert c.edges.edges == [
        (
            "objectstore:object:local/scratch/logs/app.log",
            "objectstore:bucket:local/scratch",
            {"type": "inBucket"},
        )
    ]


def test_ingest_noops_without_engine(monkeypatch):
    # No injected client, no shared primitive, no reachable engine -> clean no-op.
    monkeypatch.setattr(kg, "_shared_ingest_entities", None)
    monkeypatch.setattr(kg, "_client", lambda: (None, ""))
    assert ingest_entities([{"id": "a", "type": "Bucket"}]) is None


def test_ingest_empty_is_noop():
    assert ingest_entities([], client=_FakeClient()) is None
    assert ingest_buckets([], store="local", client=_FakeClient()) is None
    assert ingest_objects([], store="local", bucket="b", client=_FakeClient()) is None
