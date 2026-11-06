---
name: objectstore-business-asset-store
skill_type: skill
description: >-
  Run the business's durable asset store on objectstore-mcp: file generated creative outputs, video masters and social-media uploads under one key layout, tag each asset's stage, set retention, and hand an asset on to the file-share and social-scheduling steps with a presigned URL. Use when the agent must store, find, approve or hand off a business media asset. Do NOT use for generic object chores (objectstore-object-operations) or the file-share and social-scheduling steps themselves (their connectors' skills).
license: MIT
tags: [objectstore, business, media, assets, handoff, mcp]
metadata:
  author: Knuckles-Team
  version: '0.2.0'
---
# ObjectStore Business Asset Store

## Role
The object store is the system of record for business media bytes. Every other step
(the file share people review in, the social scheduler that posts) receives a copy or a
presigned URL of an object kept here, so a lost or edited copy can always be recovered.

## Key layout
| Asset | Bucket | Key | Retention |
|-------|--------|-----|-----------|
| Generated creative output | `artcraft` | `<app>/<yyyy-mm-dd>/<run>/<file>` (written by the creative suite's exchange sink) | kept |
| Video master | `video-masters` | `<project>/<yyyy-mm-dd>/<name>` | versioning Enabled; noncurrent versions expire after 90 days; stale multipart uploads abort after 7 days |
| Social-media upload | `social-media` | `<channel>/<yyyy-mm-dd>/<post-slug>/<file>` | kept |
| Scratch | any | `scratch/...` | expires after 7 days |

## Stage tags
Each asset carries the tags `stage`, `source` and, when known, `campaign`:
`stage` is `draft` (just produced), `approved` (owner approved it in the file share),
`scheduled` (a post is queued) or `published` (the post went out).

## Workflow: provision once
1. `objectstore_list_stores` and `objectstore_list_buckets`.
2. `objectstore_create_bucket` for `video-masters` and `social-media` when absent.
3. `objectstore_put_bucket_versioning bucket=video-masters status=Enabled`.
4. `objectstore_put_bucket_lifecycle` on `video-masters` with rules
   `{id: noncurrent-90d, noncurrent_expiration_days: 90}` and
   `{id: abort-multipart-7d, abort_incomplete_multipart_days: 7}`; on each bucket a
   `{id: scratch-7d, prefix: scratch/, expiration_days: 7}` rule.
5. Read both back (`objectstore_get_bucket_versioning`, `objectstore_get_bucket_lifecycle`).

## Workflow: file and tag an asset
1. Creative outputs arrive already filed under `artcraft/...`. For other assets write
   with `objectstore_put_object` (small) or `objectstore_upload_file` (server path).
2. `objectstore_put_object_tags` with `stage=draft`, `source=<craft|video|upload>`.
3. `objectstore_head_object` and report bucket, key, size and etag.

## Workflow: hand off (this connector's side)
1. Find the asset: `objectstore_list_objects` by prefix, then `objectstore_get_object_tags`.
2. Mint `objectstore_presigned_url method=GET expires_in<=604800` (7 days at most).
3. Pass `{bucket, key, etag, size, content_type, url, expires_at}` to the next step:
   the file-share step copies it into the review folder that mirrors the key path; the
   social-scheduling step uploads the media from the URL when it drafts the post.
4. When the next step reports back, update the tag: `stage=approved` after review,
   `stage=scheduled` when a post is queued, `stage=published` when it went out.
5. Never delete a master or a published asset; a correction is a new object (or a new
   version of a master).

## Find assets
- Everything awaiting review: list the bucket prefix and keep objects tagged `stage=draft`.
- Everything for a campaign: list by prefix and keep `campaign=<name>`.
- Mirror metadata into the knowledge graph for cross-source questions:
  `objectstore_ingest_objects bucket=<b> prefix=<p>` (metadata only, never bytes).

## Prerequisites & environment
Connect to the **`objectstore-mcp`** MCP server (directly, or through the fleet gateway).
Stores come from `OBJECTSTORE_STORES` (JSON); a zero-infra `local` filesystem store
always exists. Store credentials are secret references in each store's `credentials`
map; the server never reads an ambient provider chain. The caller's identity must hold
`objectstore:<store>` or `objectstore:admin` to reach a store.

| Variable | Notes |
|----------|-------|
| `OBJECTSTORE_STORES` | JSON map of named stores: backend, endpoint, `allowed_private_hosts`, `credentials` refs |
| `OBJECTSTORE_DEFAULT_STORE` | Store used when `store` is omitted (the per-operation tools always use it) |
| `OBJECTSTORE_MAX_GET_BYTES` / `OBJECTSTORE_MAX_PUT_BYTES` / `OBJECTSTORE_MAX_TRANSFER_BYTES` | Size caps |
| `OBJECTSTORE_MAX_LIST_KEYS` / `OBJECTSTORE_MAX_BATCH_KEYS` | List and batch caps |
| `OBJECTSTORE_ALLOW_DELETE` / `OBJECTSTORE_ALLOW_BUCKET_DELETE` | Delete switches (bucket deletes default off) |

## Refusals
A store failure names its code: `STORAGE_NOT_FOUND`, `STORAGE_EXISTS`,
`STORAGE_BUCKET_NOT_EMPTY`, `STORAGE_UNSUPPORTED` (for example presign or lifecycle on a
filesystem store), `STORAGE_EGRESS_REFUSED` (endpoint not in `allowed_private_hosts`),
`STORAGE_DEPENDENCY_MISSING`, or `not entitled` (the identity lacks the store role).
Report the code; do not retry a refusal unchanged.
