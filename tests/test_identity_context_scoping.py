"""Identity-scoped store auto-load (CONCEPT:AU-OS.identity.identity-scoped-resource-autoload).

The caller's entitled object stores auto-load; a non-entitled named store is
denied; the default falls to the first entitled when the configured default is
off-limits. Tests the resolution/enforcement logic with the entitlement source
mocked (the resolver itself is tested in agent-utilities).
"""

import json

import pytest

import objectstore_mcp.auth as auth


def _set_stores(monkeypatch, entitled):
    monkeypatch.setenv(
        "OBJECTSTORE_STORES",
        json.dumps(
            {
                "prod": {"backend": "s3", "bucket": "prod-bucket"},
                "dev": {"backend": "s3", "bucket": "dev-bucket"},
            }
        ),
    )
    monkeypatch.delenv("OBJECTSTORE_DEFAULT_STORE", raising=False)
    monkeypatch.setattr(
        auth,
        "entitled_store_names",
        lambda names: [n for n in names if n in entitled],
    )


def test_auto_selects_entitled_default(monkeypatch):
    # default_store_name() picks "prod" (first non-local configured store).
    _set_stores(monkeypatch, {"prod"})
    assert auth.resolve_store(None).name == "prod"


def test_default_not_entitled_falls_to_first_entitled(monkeypatch):
    _set_stores(monkeypatch, {"dev"})
    assert auth.resolve_store(None).name == "dev"


def test_named_store_not_entitled_is_denied(monkeypatch):
    _set_stores(monkeypatch, {"prod"})
    with pytest.raises(PermissionError):
        auth.resolve_store("dev")


def test_named_entitled_store_allowed(monkeypatch):
    _set_stores(monkeypatch, {"prod", "dev"})
    assert auth.resolve_store("dev").name == "dev"


def test_no_entitled_stores_raises(monkeypatch):
    _set_stores(monkeypatch, set())
    with pytest.raises(Exception, match="available to your identity"):
        auth.resolve_store(None)


def test_unknown_store_name_still_raises_unknown(monkeypatch):
    _set_stores(monkeypatch, {"prod"})
    with pytest.raises(Exception, match="Unknown store"):
        auth.resolve_store("ghost")
