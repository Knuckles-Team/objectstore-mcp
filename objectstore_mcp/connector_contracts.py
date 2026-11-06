"""Surface contracts: tool use, links, data locations and business roles."""

from scion_sdk.surface_contracts import (
    BusinessRole,
    DataLocation,
    Refusal,
    SurfaceLink,
    ToolStep,
    ToolUseContract,
)

CONTRACTS = (
    ToolUseContract(
        task="inspect-store-capabilities",
        description="List the configured stores and what the connected store supports.",
        steps=(
            ToolStep(
                tool="objectstore_list_stores",
                params=(),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="NOT_FOUND", when="the requested record does not exist"
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_capabilities",
                params=(),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        task="inspect-buckets",
        description="Find a bucket and read its state before touching it.",
        steps=(
            ToolStep(
                tool="objectstore_list_buckets",
                params=(),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="NOT_FOUND", when="the requested record does not exist"
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_bucket_exists",
                params=("bucket",),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_bucket_info",
                params=("bucket",),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        task="provision-bucket",
        description="Create a bucket with versioning and lifecycle rules.",
        steps=(
            ToolStep(
                tool="objectstore_bucket_exists",
                params=("bucket",),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_create_bucket",
                params=(
                    "bucket",
                    "location",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_get_bucket_versioning",
                params=(
                    "bucket",
                    "store",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="NOT_FOUND", when="the requested record does not exist"
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_put_bucket_versioning",
                params=(
                    "bucket",
                    "status",
                    "store",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_get_bucket_lifecycle",
                params=(
                    "bucket",
                    "store",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="NOT_FOUND", when="the requested record does not exist"
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_put_bucket_lifecycle",
                params=(
                    "bucket",
                    "rules",
                    "store",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        task="retire-bucket-policy",
        description="Remove a lifecycle policy or an empty bucket after approval.",
        steps=(
            ToolStep(
                tool="objectstore_get_bucket_lifecycle",
                params=(
                    "bucket",
                    "store",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="NOT_FOUND", when="the requested record does not exist"
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_delete_bucket_lifecycle",
                params=(
                    "bucket",
                    "store",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                    Refusal(
                        code="CONFIRMATION_REQUIRED",
                        when="the caller has not confirmed the destructive call",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_delete_bucket",
                params=(
                    "bucket",
                    "confirm",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                    Refusal(
                        code="CONFIRMATION_REQUIRED",
                        when="the caller has not confirmed the destructive call",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        task="browse-objects",
        description="List objects under a prefix and read their headers and metadata.",
        steps=(
            ToolStep(
                tool="objectstore_list_objects",
                params=(
                    "bucket",
                    "continuation_token",
                    "delimiter",
                    "max_keys",
                    "prefix",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="NOT_FOUND", when="the requested record does not exist"
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_head_object",
                params=(
                    "bucket",
                    "key",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_get_object_metadata",
                params=(
                    "bucket",
                    "key",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="NOT_FOUND", when="the requested record does not exist"
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        task="read-object",
        description="Read an object's content or hand it on by presigned URL.",
        steps=(
            ToolStep(
                tool="objectstore_head_object",
                params=(
                    "bucket",
                    "key",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_get_object",
                params=(
                    "bucket",
                    "key",
                    "max_bytes",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="NOT_FOUND", when="the requested record does not exist"
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_presigned_url",
                params=(
                    "bucket",
                    "expires_in",
                    "key",
                    "method",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="NOT_FOUND", when="the requested record does not exist"
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        task="file-business-asset",
        description="Store a business asset under the key layout, tag its stage and verify it.",
        steps=(
            ToolStep(
                tool="objectstore_list_stores",
                params=(),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="NOT_FOUND", when="the requested record does not exist"
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_put_object",
                params=(
                    "bucket",
                    "content_type",
                    "data",
                    "key",
                    "metadata",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_upload_file",
                params=(
                    "bucket",
                    "content_type",
                    "key",
                    "local_path",
                    "metadata",
                    "store",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_put_object_tags",
                params=(
                    "bucket",
                    "key",
                    "store",
                    "tags",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_get_object_tags",
                params=(
                    "bucket",
                    "key",
                    "store",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="NOT_FOUND", when="the requested record does not exist"
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_head_object",
                params=(
                    "bucket",
                    "key",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_set_object_metadata",
                params=(
                    "bucket",
                    "key",
                    "metadata",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_presigned_url",
                params=(
                    "bucket",
                    "expires_in",
                    "key",
                    "method",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="NOT_FOUND", when="the requested record does not exist"
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        task="retag-or-relocate-object",
        description="Change an object's stage tags, remove tags, copy or move it.",
        steps=(
            ToolStep(
                tool="objectstore_head_object",
                params=(
                    "bucket",
                    "key",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_get_object_tags",
                params=(
                    "bucket",
                    "key",
                    "store",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="NOT_FOUND", when="the requested record does not exist"
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_put_object_tags",
                params=(
                    "bucket",
                    "key",
                    "store",
                    "tags",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_delete_object_tags",
                params=(
                    "bucket",
                    "key",
                    "store",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                    Refusal(
                        code="CONFIRMATION_REQUIRED",
                        when="the caller has not confirmed the destructive call",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_copy_object",
                params=(
                    "dst_bucket",
                    "dst_key",
                    "src_bucket",
                    "src_key",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_move_object",
                params=(
                    "dst_bucket",
                    "dst_key",
                    "src_bucket",
                    "src_key",
                    "store",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                    Refusal(
                        code="CONFIRMATION_REQUIRED",
                        when="the caller has not confirmed the destructive call",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        task="delete-objects",
        description="Delete one object or all objects under a prefix after a dry run and approval.",
        steps=(
            ToolStep(
                tool="objectstore_list_objects",
                params=(
                    "bucket",
                    "continuation_token",
                    "delimiter",
                    "max_keys",
                    "prefix",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="NOT_FOUND", when="the requested record does not exist"
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_delete_object",
                params=(
                    "bucket",
                    "confirm",
                    "key",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                    Refusal(
                        code="CONFIRMATION_REQUIRED",
                        when="the caller has not confirmed the destructive call",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_delete_objects_by_prefix",
                params=(
                    "bucket",
                    "dry_run",
                    "max_keys",
                    "prefix",
                    "store",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                    Refusal(
                        code="CONFIRMATION_REQUIRED",
                        when="the caller has not confirmed the destructive call",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        task="transfer-files",
        description="Upload or download files and directories between local disk and a bucket.",
        steps=(
            ToolStep(
                tool="objectstore_bucket_exists",
                params=("bucket",),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_upload_directory",
                params=(
                    "bucket",
                    "local_dir",
                    "max_keys",
                    "prefix",
                    "store",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_download_file",
                params=(
                    "bucket",
                    "key",
                    "local_path",
                    "overwrite",
                    "store",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_download_prefix",
                params=(
                    "bucket",
                    "local_dir",
                    "max_keys",
                    "overwrite",
                    "prefix",
                    "store",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
        ),
    ),
    ToolUseContract(
        task="mirror-store-to-graph",
        description="Land buckets and objects in the knowledge graph.",
        steps=(
            ToolStep(
                tool="objectstore_ingest_buckets",
                params=("store",),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
            ToolStep(
                tool="objectstore_ingest_objects",
                params=(
                    "bucket",
                    "max_keys",
                    "prefix",
                    "store",
                ),
                result=("result",),
                refusals=(
                    Refusal(
                        code="ACCESS_DENIED",
                        when="the credential lacks access to the operation",
                    ),
                    Refusal(
                        code="INVALID_ARGUMENT",
                        when="the upstream system rejects the input",
                    ),
                ),
            ),
        ),
    ),
)

LINKS = (
    SurfaceLink(
        task="inspect-store-capabilities",
        tools=(
            "objectstore_list_stores",
            "objectstore_capabilities",
        ),
        prompts=(
            "objectstore-operator",
            "objectstore_asset_librarian",
            "objectstore-storage-administrator",
        ),
        skills=(
            "objectstore-bucket-administration",
            "objectstore-mcp-operations",
        ),
    ),
    SurfaceLink(
        task="inspect-buckets",
        tools=(
            "objectstore_list_buckets",
            "objectstore_bucket_exists",
            "objectstore_bucket_info",
        ),
        prompts=(
            "objectstore-operator",
            "objectstore-storage-administrator",
        ),
        skills=("objectstore-bucket-administration",),
    ),
    SurfaceLink(
        task="provision-bucket",
        tools=(
            "objectstore_bucket_exists",
            "objectstore_create_bucket",
            "objectstore_get_bucket_versioning",
            "objectstore_put_bucket_versioning",
            "objectstore_get_bucket_lifecycle",
            "objectstore_put_bucket_lifecycle",
        ),
        prompts=(
            "objectstore-operator",
            "objectstore-storage-administrator",
        ),
        skills=(
            "objectstore-bucket-administration",
            "objectstore-business-asset-store",
        ),
    ),
    SurfaceLink(
        task="retire-bucket-policy",
        tools=(
            "objectstore_get_bucket_lifecycle",
            "objectstore_delete_bucket_lifecycle",
            "objectstore_delete_bucket",
        ),
        prompts=(
            "objectstore-operator",
            "objectstore-storage-administrator",
        ),
        skills=("objectstore-bucket-administration",),
    ),
    SurfaceLink(
        task="browse-objects",
        tools=(
            "objectstore_list_objects",
            "objectstore_head_object",
            "objectstore_get_object_metadata",
        ),
        prompts=(
            "objectstore-operator",
            "objectstore_asset_librarian",
        ),
        skills=("objectstore-object-operations",),
    ),
    SurfaceLink(
        task="read-object",
        tools=(
            "objectstore_head_object",
            "objectstore_get_object",
            "objectstore_presigned_url",
        ),
        prompts=(
            "objectstore-operator",
            "objectstore_asset_librarian",
        ),
        skills=(
            "objectstore-object-operations",
            "objectstore-business-asset-store",
        ),
    ),
    SurfaceLink(
        task="file-business-asset",
        tools=(
            "objectstore_list_stores",
            "objectstore_put_object",
            "objectstore_upload_file",
            "objectstore_put_object_tags",
            "objectstore_get_object_tags",
            "objectstore_head_object",
            "objectstore_set_object_metadata",
            "objectstore_presigned_url",
        ),
        prompts=(
            "objectstore-operator",
            "objectstore_asset_librarian",
        ),
        skills=(
            "objectstore-business-asset-store",
            "objectstore-object-operations",
        ),
    ),
    SurfaceLink(
        task="retag-or-relocate-object",
        tools=(
            "objectstore_head_object",
            "objectstore_get_object_tags",
            "objectstore_put_object_tags",
            "objectstore_delete_object_tags",
            "objectstore_copy_object",
            "objectstore_move_object",
        ),
        prompts=(
            "objectstore-operator",
            "objectstore_asset_librarian",
        ),
        skills=(
            "objectstore-object-operations",
            "objectstore-business-asset-store",
        ),
    ),
    SurfaceLink(
        task="delete-objects",
        tools=(
            "objectstore_list_objects",
            "objectstore_delete_object",
            "objectstore_delete_objects_by_prefix",
        ),
        prompts=(
            "objectstore-operator",
            "objectstore-storage-administrator",
        ),
        skills=("objectstore-object-operations",),
    ),
    SurfaceLink(
        task="transfer-files",
        tools=(
            "objectstore_bucket_exists",
            "objectstore_upload_directory",
            "objectstore_download_file",
            "objectstore_download_prefix",
        ),
        prompts=(
            "objectstore-operator",
            "objectstore-storage-administrator",
        ),
        skills=("objectstore-data-transfer",),
    ),
    SurfaceLink(
        task="mirror-store-to-graph",
        tools=(
            "objectstore_ingest_buckets",
            "objectstore_ingest_objects",
        ),
        prompts=(
            "objectstore-operator",
            "objectstore_asset_librarian",
            "objectstore-storage-administrator",
        ),
        skills=(
            "objectstore-bucket-administration",
            "objectstore-business-asset-store",
        ),
    ),
)

LOCATIONS = (
    DataLocation(
        name="objectstore-objects",
        holds=("Object",),
        instance="objectstore-mcp-default",
        read_tool="objectstore_list_objects",
    ),
    DataLocation(
        name="objectstore-buckets",
        holds=("Bucket",),
        instance="objectstore-mcp-default",
        read_tool="objectstore_list_buckets",
    ),
)

ROLES = (
    BusinessRole(
        name="asset-librarian",
        tasks=(
            "inspect-store-capabilities",
            "browse-objects",
            "read-object",
            "file-business-asset",
            "retag-or-relocate-object",
            "mirror-store-to-graph",
        ),
        description="Files, tags, retains and hands off business media assets kept in object storage.",
    ),
    BusinessRole(
        name="storage-administrator",
        tasks=(
            "inspect-store-capabilities",
            "inspect-buckets",
            "provision-bucket",
            "retire-bucket-policy",
            "delete-objects",
            "transfer-files",
            "mirror-store-to-graph",
        ),
        description="Provisions buckets, retention and versioning, moves bulk data and removes data with approval.",
    ),
)
