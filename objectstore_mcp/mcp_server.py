"""Main FastMCP server and tool registration for objectstore-mcp."""

import sys
from typing import Any

from agent_utilities.mcp_utilities import create_mcp_server
from dotenv import find_dotenv, load_dotenv
from fastmcp.utilities.logging import get_logger
from starlette.requests import Request
from starlette.responses import JSONResponse

from objectstore_mcp import __version__
from objectstore_mcp.mcp.mcp_objectstore import register_objectstore_tools

logger = get_logger(name="objectstore_mcp")


def get_mcp_instance() -> tuple[Any, ...]:
    load_dotenv(find_dotenv())
    args, mcp, middlewares = create_mcp_server(
        name="ObjectStore MCP",
        version=__version__,
        instructions=(
            "Object-storage MCP server - one tool surface over S3 and "
            "S3-compatible stores (MinIO/R2), Google Cloud Storage, Azure "
            "Blob, and a zero-infra local-filesystem backend. Tools: "
            "'objects' (list/head/get/put/copy/move/delete/presign/metadata), "
            "'buckets' (list/create/delete/exists/info/stores), 'transfer' "
            "(upload/download, single or by prefix). Named stores come from "
            "OBJECTSTORE_STORES; the 'local' filesystem store always exists."
        ),
    )

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        return JSONResponse({"status": "OK"})

    register_objectstore_tools(mcp)

    for mw in middlewares:
        mcp.add_middleware(mw)
    return mcp, args, middlewares


def mcp_server() -> None:
    mcp, args, _middlewares = get_mcp_instance()
    print(f"ObjectStore MCP v{__version__}", file=sys.stderr)
    if args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    mcp_server()
