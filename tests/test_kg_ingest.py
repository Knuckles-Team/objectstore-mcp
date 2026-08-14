"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``ingest_entities`` / ``ingest_buckets`` / ``ingest_objects`` seam
with a fake engine client (no engine required), asserting the txn add_node/commit +
edge calls and the object-store record → :ObjectStore/:Bucket/:Object mapping.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from typing import Any

import msgpack
import pytest
from agent_utilities.knowledge_graph.memory.native_ingest import NativeIngestError
from agent_utilities.security.brain_context import ActorContext, use_actor
from agent_utilities.models.company_brain import ActorType
from agent_utilities.knowledge_graph.core.session import GraphSession, use_session

from objectstore_mcp.kg_ingest import ingest_buckets, ingest_entities, ingest_objects


@pytest.fixture(autouse=True)
def _governed_session():
    actor = ActorContext(
        actor_id="subject:opaque:synthetic",
        actor_type=ActorType.AUTOMATED_SERVICE,
        roles=(),
        tenant_id="tenant:opaque:synthetic",
        authenticated=True,
    )
    session = GraphSession(
        actor=actor,
        tenant=actor.tenant_id,
        scopes=frozenset({"kg:write"}),
        graph="graph:opaque:synthetic",
        policy_version="policy:opaque:synthetic",
        audience="epistemic-graph",
    )
    with use_actor(actor), use_session(session):
        yield


class _FakeNodes:
    def __init__(self) -> None:
        self.values: dict[str, dict[str, Any]] = {}

    def properties(self, node_id: str) -> dict[str, Any] | None:
        return self.values.get(node_id)

    def list(self) -> list[tuple[str, dict[str, Any]]]:
        return list(self.values.items())


class _FakeChanges:
    def __init__(self, nodes: _FakeNodes) -> None:
        self.nodes = nodes
        self.edges: list[tuple[str, str, dict[str, Any]]] = []
        self.applied: list[dict[str, Any]] = []
        self.records: dict[str, dict[str, Any]] = {}
        self.versions: dict[str, dict[str, Any]] = {}

    def get(self, envelope_id: str) -> dict[str, Any] | None:
        return self.records.get(envelope_id)

    def content_version(self, object_id: str) -> dict[str, Any] | None:
        return self.versions.get(object_id)

    def cursor(self, _source: str, _partition: str = "") -> None:
        return None

    def apply(self, envelope: dict[str, Any]) -> dict[str, Any]:
        self.applied.append(envelope)
        mutation = envelope["mutation"]
        for operation in mutation["operations"]:
            method = operation["method"]
            params = method["params"]
            properties = msgpack.unpackb(params["properties_msgpack"], raw=False)
            if method["method"] == "AddNode":
                self.nodes.values[params["node_id"]] = properties
            elif method["method"] == "AddEdge":
                self.edges.append(
                    (params["source_id"], params["target_id"], properties)
                )
        version = envelope["content_version"]
        self.versions[version["object_id"]] = version
        self.records[envelope["envelope_id"]] = envelope
        return {
            "batch_id": mutation["batch_id"],
            "replayed": False,
            "projection_pending": False,
        }


class _FakeRdf:
    def validate_shacl(self, _shapes: str, _data_graph: str) -> dict[str, Any]:
        return {"conforms": True, "results": []}


class _FakeClient:
    def __init__(self) -> None:
        self.nodes = _FakeNodes()
        self.changes = _FakeChanges(self.nodes)
        self.rdf = _FakeRdf()

    @staticmethod
    def supports(operation: str) -> bool:
        return operation == "ApplyChangeEnvelope"


def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
        [
            {"id": "a", "node_type": "Bucket", "name": "b"},
            {"id": "s", "node_type": "ObjectStore"},
        ],
        [{"source": "a", "target": "s", "relationship": "inStore"}],
        client=c,
    )
    assert res == {"nodes": 2, "edges": 1}
    assert len(c.changes.applied) == 1
    assert set(c.nodes.values) == {"a", "s"}
    # provenance is stamped
    assert c.nodes.values["a"]["source"] == "objectstore-mcp"
    assert c.nodes.values["a"]["domain"] == "objectstore"
    assert c.changes.edges == [("a", "s", {"relationship": "inStore"})]


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
    )
    # 1 store node + 2 bucket nodes; 2 inStore edges
    assert res == {"nodes": 3, "edges": 2}
    store_node = c.nodes.values["objectstore:store:minio"]
    assert store_node["node_type"] == "ObjectStore"
    assert store_node["backendType"] == "s3"
    # native_ingest's governed PII scrubber redacts uri-shaped values.
    assert store_node["endpoint"] == "[REDACTED_LOCATION]"
    bucket_node = c.nodes.values["objectstore:bucket:minio/media-prod"]
    assert bucket_node["node_type"] == "Bucket"
    assert bucket_node["location"] == "us"
    assert bucket_node["externalToolId"] == "minio/media-prod"
    assert (
        "objectstore:bucket:minio/media-prod",
        "objectstore:store:minio",
        {"relationship": "inStore"},
    ) in c.changes.edges


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
    )
    # 1 bucket node + 1 object node; 1 inBucket edge
    assert res == {"nodes": 2, "edges": 1}
    obj = c.nodes.values["objectstore:object:local/scratch/logs/app.log"]
    assert obj["node_type"] == "Object"
    assert obj["objectKey"] == "logs/app.log"
    assert obj["byteSize"] == 1234
    assert obj["contentType"] == "text/plain"
    assert obj["storageClass"] == "STANDARD"
    assert c.nodes.values["objectstore:bucket:local/scratch"]["node_type"] == "Bucket"
    assert c.changes.edges == [
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
