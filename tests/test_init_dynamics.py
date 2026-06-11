import importlib


def test_package_imports():
    module = importlib.import_module("objectstore_mcp")
    assert hasattr(module, "__all__")
