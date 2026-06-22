"""Shared pytest fixtures.

Model round-trip tests run without a database. Repository tests need a reachable
MongoDB; they connect via the standard ``MONGO_*`` env vars (defaulting to a local
``qhlddb_test`` database) and are skipped when no server is available.

``MONGO_SKIP_INDEX_INIT`` is set before importing ``tipi_data`` so that importing
the package never blocks on a connection during DB-free test runs.
"""

import os

os.environ.setdefault("MONGO_SKIP_INDEX_INIT", "1")
os.environ.setdefault("MONGO_HOST", "localhost")
os.environ.setdefault("MONGO_DB_NAME", "qhlddb_test")

import pytest
from pymongo.errors import PyMongoError

from tipi_data import client, db, ensure_indexes


@pytest.fixture
def mongo_db():
    """A reachable test database, or skip the test. Drops all collections before
    yielding so each test starts clean, and creates the declared indexes."""
    try:
        client.admin.command("ping")
    except PyMongoError:
        pytest.skip("No MongoDB reachable for repository integration tests")

    for name in db.list_collection_names():
        db.drop_collection(name)
    ensure_indexes()
    yield db
    for name in db.list_collection_names():
        db.drop_collection(name)
