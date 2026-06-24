"""Footprint serialization tests for the deputy / parliamentary-group schemas.

These cover the correctness fix (footprints are looked up via pymongo, not the
removed mongoengine ``.objects`` manager) and the N+1 fix (a list serializes with
a single footprint query). They need a reachable MongoDB via the ``mongo_db``
fixture and are skipped otherwise.
"""

import pytest

from tipi_data.repositories.deputies import Deputies
from tipi_data.repositories.footprints import Footprints
from tipi_data.repositories.parliamentarygroups import ParliamentaryGroups
from tipi_data.schemas.deputy import DeputySchema
from tipi_data.schemas.parliamentarygroup import ParliamentaryGroupSchema

pytestmark = pytest.mark.integration


def _seed_deputies(db):
    db.deputies.insert_many([
        {"_id": "d1", "name": "With Footprint", "parliamentarygroup": "G", "active": True},
        {"_id": "d2", "name": "Without Footprint", "parliamentarygroup": "G", "active": True},
    ])
    # footprint_by_deputies is keyed by the deputy id (see qhld-engine).
    db.footprint_by_deputies.insert_one({
        "_id": "d1", "name": "With Footprint", "score": 7.5,
        "topics": [{"name": "Salud", "score": 5.0}, {"name": "Empleo", "score": 2.5}],
    })


def test_deputy_from_doc_uses_real_footprint(mongo_db):
    _seed_deputies(mongo_db)
    d1 = Deputies.get("d1")

    out = DeputySchema.from_doc(d1)
    assert out.footprint == 7.5
    assert {t.name for t in out.footprint_by_topics} == {"Salud", "Empleo"}


def test_deputy_from_doc_missing_footprint_is_zero(mongo_db):
    _seed_deputies(mongo_db)
    d2 = Deputies.get("d2")

    out = DeputySchema.from_doc(d2)
    assert out.footprint == 0.0
    assert out.footprint_by_topics == []


def test_deputy_from_docs_batches_into_single_query(mongo_db, monkeypatch):
    _seed_deputies(mongo_db)
    deputies = Deputies.get_by_query({})
    assert len(deputies) == 2

    # The list path must use the batched lookup exactly once and never fall back
    # to the per-row (N+1) lookup.
    calls = {"batch": 0, "per_row": 0}
    real_batch = Footprints.get_by_deputy_ids

    def counting_batch(ids):
        calls["batch"] += 1
        return real_batch(ids)

    def counting_per_row(id):
        calls["per_row"] += 1
        raise AssertionError("from_docs must not do per-row footprint lookups")

    monkeypatch.setattr(Footprints, "get_by_deputy_ids", staticmethod(counting_batch))
    monkeypatch.setattr(Footprints, "get_by_deputy_id", staticmethod(counting_per_row))

    out = DeputySchema.from_docs(deputies)

    assert calls["batch"] == 1   # one query for the whole list...
    assert calls["per_row"] == 0  # ...not one per deputy
    by_id = {o.id: o for o in out}
    assert by_id["d1"].footprint == 7.5
    assert by_id["d2"].footprint == 0.0
    assert [o.id for o in out] == [d.id for d in deputies]  # order preserved


def test_parliamentarygroup_footprint_serialization(mongo_db):
    mongo_db.parliamentarygroups.insert_many([
        {"_id": "g1", "name": "Group One", "shortname": "G1"},
        {"_id": "g2", "name": "Group Two", "shortname": "G2"},
    ])
    mongo_db.footprint_by_parliamentarygroups.insert_one({
        "_id": "g1", "name": "Group One", "score": 9.0,
        "topics": [{"name": "Salud", "score": 9.0}],
    })

    groups = ParliamentaryGroups.get_by_query({})
    out = {o.id: o for o in ParliamentaryGroupSchema.from_docs(groups)}

    assert out["g1"].footprint == 9.0
    assert {t.name for t in out["g1"].footprint_by_topics} == {"Salud"}
    assert out["g2"].footprint == 0.0
    assert out["g2"].footprint_by_topics == []
