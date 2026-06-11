# Backing Platform — Object Stores

`objectstore-mcp` is a **client** of one or more object stores. The local
filesystem backend needs no platform at all; for the cloud backends, the
recipes below run local, API-compatible stand-ins that serve as targets of
`OBJECTSTORE_STORES`.

!!! note "Backing-system recipe"
    Each connector in the ecosystem follows the same convention — a
    `docs/platform.md` recipe for the system it integrates with, accompanied by a
    sample Compose stack. Systems offered only as a managed service have no local
    recipe.

## Single-node deployment (Compose)

```yaml
# platform.compose.yml — pick the providers you need
services:
  minio:                       # S3-compatible
    image: minio/minio:latest
    restart: unless-stopped
    command: server /data --console-address ":9090"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: change-me
    ports:
      - "9000:9000"
      - "9090:9090"
    volumes:
      - minio-data:/data

  azurite:                     # Azure Blob emulator
    image: mcr.microsoft.com/azure-storage/azurite:latest
    restart: unless-stopped
    command: azurite-blob --blobHost 0.0.0.0
    ports:
      - "10000:10000"

  fake-gcs:                    # Google Cloud Storage emulator
    image: fsouza/fake-gcs-server:latest
    restart: unless-stopped
    command: -scheme http
    ports:
      - "4443:4443"

volumes:
  minio-data:
```

Matching store registry:

```bash
OBJECTSTORE_STORES={"minio": {"backend": "s3", "endpoint": "http://localhost:9000"}, "azurite": {"backend": "azure", "connection_string": "UseDevelopmentStorage=true"}}
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=change-me
```

The zero-infra `local` store (rooted at `OBJECTSTORE_FS_ROOT`) is always
available without any of the above.
