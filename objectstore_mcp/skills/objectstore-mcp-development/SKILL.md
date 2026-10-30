---
name: objectstore-mcp-development
skill_type: skill
domain: development
description: >-
  Develop, test, gate, and release the objectstore-mcp connector. Use this skill
  when changing object-storage backends, action-routed MCP tools, connector
  content, packaging, documentation, or repository gates.
license: MIT
tags: [objectstore, development, connector, test, gates]
tier: repository
metadata:
  author: Knuckles-Team
  version: '0.1.0'
---

# objectstore-mcp development

This repository owns the object-storage backends, safety-governed action-routed
MCP tools, connector content, and source declarations for S3-compatible stores,
GCS, Azure Blob, and the local filesystem backend. Shared MCP contracts,
transports, and source-ingest clients belong to `scion-sdk`;
admission, serving, and durable graph state belong to their owning repositories.
Read `AGENTS.md` before changing code. Keep credentials, customer objects,
private endpoints, bucket names, and raw object data out of source, logs,
fixtures, and packaged skill content.

## Rapid delivery: the 5-minute contract

Specs are already designed. Deliver small, reviewable slices and cite the
owning spec row in the commit trailer.

- Find the owning row first with `git grep -n "<term>" -- specs`; extend the
  existing spec before adding requirement text.
- Reuse the SDK `Connector`, the existing backend protocol, and the action-routed
  `objects`, `buckets`, and `transfer` tools. Do not create a second connector
  entry point, transport, graph-write path, or parallel safety policy.
- Keep provider SDK imports lazy and preserve the `ObjectStoreBackend` conformance
  contract. Safety caps, delete guards, and dry-run behavior remain in
  `objectstore_mcp/mcp/mcp_objectstore.py`, not in provider adapters.
- Bind delivered behavior to a focused test. Generated `specs/*/status.json`
  files come from the shared hooks; never hand-edit them.
- Keep `skills/**`, `ontology/**`, `connectors/**`, prompts, and manifest content
  in the package-data contract. Put `Spec: <ID>` and the assisting-agent trailer
  on consecutive final commit message lines.

## Setup and gates

Use the pinned environment and shared gates from the checkout root:

```bash
uv sync --locked
uvx pre-commit run --all-files
```

For focused feedback, use the tests that exercise the actual connector paths:

```bash
uv run --locked --extra test pytest tests/test_publication_workflow.py -q
uv run --locked --extra test pytest tests/test_objectstore_mcp_validation.py tests/test_backend_conformance.py -q
uv run --locked --extra test pytest tests/test_auth.py tests/test_api_wrapper.py tests/test_safety.py -q
```

Tests use the filesystem backend and temporary directories. Do not call a live
cloud provider or require credentials in local gates. `OBJECTSTORE_STORES`,
`OBJECTSTORE_DEFAULT_STORE`, `OBJECTSTORE_FS_ROOT`, and the provider SDK
credential chains are runtime inputs. Preserve the condensed/verbose SDK tool
modes, TLS and auth delegation, explicit bucket/delete checks, size/key caps,
and ontology/source mappings when changing backend or tool modules.

## Packaging and publication

Build with `uv build` and inspect the wheel and sdist for
`objectstore_mcp/skills/objectstore-mcp-development/SKILL.md`. Keep the project
version and `uv.lock` aligned for a genuine content release. The canonical Pages
publisher is `.github/workflows/pages.yml`, which calls the shared pipelines
workflow with `.config/spec-dashboard.json`; keep its `workflow_dispatch` path
and do not add another documentation publisher. The generated dashboard reads
`specs/*/status.json` and is published at `spec-delivery/`.

Before pushing, work in a real Git worktree based on `origin/main`, inspect the
complete diff, stage only reviewed paths, and verify `git status --short` after
each gate. Do not use `git stash`, `git add -A`, `git add .`, or force-push. Do
not claim Pages publication until a successful exact-source workflow run and the
public dashboard are both observed.
