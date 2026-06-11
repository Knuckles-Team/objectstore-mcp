"""objectstore-mcp — multi-backend object-storage API + MCP Server + A2A Agent.

One MCP tool surface (objects/buckets/transfer) over S3 and S3-compatible
stores (MinIO, Cloudflare R2), Google Cloud Storage, Azure Blob Storage, and
a zero-infra local-filesystem backend (CONCEPT:OBJ-1.0).
"""

import importlib
import inspect
from typing import Any

__version__ = "0.1.0"
__all__: list[str] = []

CORE_MODULES = ["objectstore_mcp.api_client"]
OPTIONAL_MODULES = {
    "objectstore_mcp.agent_server": "agent",
    "objectstore_mcp.mcp_server": "mcp",
}


def _expose_members(module):
    for name, obj in inspect.getmembers(module):
        if (inspect.isclass(obj) or inspect.isfunction(obj)) and not name.startswith(
            "_"
        ):
            globals()[name] = obj
            if name not in __all__:
                __all__.append(name)


for module_name in CORE_MODULES:
    module = importlib.import_module(module_name)
    _expose_members(module)

_loaded_optional_modules = {}


def _import_module_safely(module_name: str):
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


def __getattr__(name: str) -> Any:
    if name == "_MCP_AVAILABLE":
        mcp_key = next((k for k in OPTIONAL_MODULES if "mcp_server" in k), None)
        return _import_module_safely(mcp_key) is not None if mcp_key else False
    if name == "_AGENT_AVAILABLE":
        agent_key = next((k for k in OPTIONAL_MODULES if "agent_server" in k), None)
        return _import_module_safely(agent_key) is not None if agent_key else False

    for module_name in OPTIONAL_MODULES:
        if module_name not in _loaded_optional_modules:
            module = _import_module_safely(module_name)
            _loaded_optional_modules[module_name] = module
            if module is not None:
                _expose_members(module)
        module = _loaded_optional_modules[module_name]
        if module is not None and hasattr(module, name):
            return getattr(module, name)
    raise AttributeError(f"module 'objectstore_mcp' has no attribute {name!r}")
