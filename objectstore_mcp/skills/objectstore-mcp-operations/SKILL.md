---
name: objectstore-mcp-operations
skill_type: skill
description: >-
  Operate objectstore-mcp through its governed MCP and Arbora capabilities, including bucket administration and lifecycle, data transfer, object operations and the business asset store. Use when a request requires this provider's read, change, automation, ingestion, troubleshooting, or evidence workflows.
---

# Objectstore Mcp Operations

Use the provider's governed MCP tools through Arbora delegation.

## Workflow

1. Establish the verified GraphSession and tenant before discovery or retrieval.
2. Discover the current typed tool surface (one tool per operation); never assume a stale tool name or schema.
3. Prefer read-only inspection first. For changes, present impact and use the provider's
   dry-run or preview mode when available.
4. Execute mutations as fenced WorkItems so retries remain idempotent and auditable.
5. Ingest source data only through the signed connector preset and ChangeEnvelope path.
6. Verify the durable result and its trace/evidence before reporting completion.

## Steps

1. Establish the verified GraphSession and tenant, and discover the tool surface with the fleet `find` call.
   Verify the typed `objectstore_*` tool you need is listed before use.
2. Run read-only inspection first, such as `objectstore_list_buckets` or `objectstore_list_objects`.
   Verify the target store and bucket appear in the result.
3. For a change, preview impact and use dry-run where offered, for example `objectstore_delete_objects_by_prefix` with `dry_run=true`.
   Verify the preview lists only the intended keys.
4. Execute the mutation as a fenced WorkItem with the typed tool, for example `objectstore_put_object`.
   Verify the response names the changed keys or buckets.
5. Confirm the durable result with `objectstore_head_object` or `objectstore_get_bucket_lifecycle` and cite the trace.
   Verify the stored state matches the request before reporting.

## Failure recovery

| Failure | Cause | Recovery |
|---------|-------|----------|
| Tool name or schema not found | The tool list was assumed rather than discovered | Rediscover the typed tool surface through the fleet `find` call, and use the exact name returned |
| `not entitled` or unknown ACL | The identity lacks the store role, or tenant state is unclear | Treat it as a hard failure, report the code, and ask the operator for the store role |
| Destructive call refused | No explicit approval or `confirm=true` was given | Obtain explicit approval, and repeat the call with `confirm=true` after a dry run |

## Safety contract

- Never persist credentials, endpoints, raw personal identifiers, hostnames, or local paths.
- Resolve TLS trust and verification from environment/configuration; never hardcode bypasses.
- Treat unknown ACL, tenant, schema, or tool-contract state as a hard failure.
- Require explicit approval for destructive, externally visible, or irreversible actions.
- Keep runtime traces policy-scoped and privacy-sanitized.

## Specialized workflows

Read [the workflow catalog](references/catalog.md) only when the request needs a
provider-specific procedure, parameter map, script, or reference asset.
