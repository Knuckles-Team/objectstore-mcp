# Installation

## PyPI

```bash
pip install objectstore-mcp            # core: local filesystem backend only
pip install objectstore-mcp[s3]        # + boto3 (AWS S3, MinIO, Cloudflare R2)
pip install objectstore-mcp[gcs]       # + google-cloud-storage
pip install objectstore-mcp[azure]     # + azure-storage-blob
pip install objectstore-mcp[all]       # every cloud backend
```

The core install carries **zero cloud dependencies**: only the filesystem
backend is importable, and constructing a cloud backend without its SDK
raises a `MissingDependencyError` that names the extra to install.

## Credentials

| Backend | Resolution |
|---|---|
| S3 / MinIO / R2 | boto3's standard chain: `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`, `~/.aws` config (per-store `profile`), SSO, instance metadata. Per-store `endpoint` targets MinIO/R2. |
| GCS | Application Default Credentials: `GOOGLE_APPLICATION_CREDENTIALS` service-account file, gcloud user credentials, or workload identity. |
| Azure Blob | `AZURE_STORAGE_CONNECTION_STRING` (or a per-store `connection_string` option). |
| Filesystem | None. Root directory from the store's `root` or `OBJECTSTORE_FS_ROOT`. |

## Docker

```bash
docker compose -f docker/compose.yml up --build     # build from source
docker compose -f docker/mcp.compose.yml up         # published image
```

Both run the server on streamable-http at port 8000 with the `local` store
persisted in the `objectstore-data` volume.

## Development install

```bash
pip install -e .[test]       # core + pytest stack (no cloud SDKs needed)
pip install -e .[test-s3]    # adds boto3 + moto for S3 integration tests
pytest
pre-commit run --all-files
```
