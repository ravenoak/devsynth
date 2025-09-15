"""Focused tests for RDFLibStore transaction helpers."""

import os
import uuid

import pytest

from devsynth.application.memory import rdflib_store

pytestmark = [pytest.mark.fast, pytest.mark.requires_resource("rdflib")]


if os.environ.get("DEVSYNTH_RESOURCE_RDFLIB_AVAILABLE", "true").lower() == "false":
    pytest.skip("RDFLib resource not available", allow_module_level=True)


def test_begin_transaction_returns_existing_identifier():
    """Providing an explicit identifier should be returned untouched."""

    store = rdflib_store.RDFLibStore.__new__(rdflib_store.RDFLibStore)
    assert store.begin_transaction("txn-123") == "txn-123"


def test_begin_transaction_generates_uuid(monkeypatch):
    """When no identifier is supplied the store should generate a UUID string."""

    store = rdflib_store.RDFLibStore.__new__(rdflib_store.RDFLibStore)
    generated = uuid.UUID("12345678-1234-5678-1234-567812345678")
    monkeypatch.setattr(rdflib_store.uuid, "uuid4", lambda: generated)

    assert store.begin_transaction() == str(generated)


def test_transaction_methods_are_noops():
    """Commit, rollback, and activity checks should behave as documented no-ops."""

    store = rdflib_store.RDFLibStore.__new__(rdflib_store.RDFLibStore)

    assert store.commit_transaction("txn-any") is True
    assert store.rollback_transaction("txn-any") is True
    assert store.is_transaction_active("txn-any") is False
