"""Repository integration tests against a real MongoDB (skipped if none reachable).

Each test seeds the collections it needs via the ``mongo_db`` fixture, then exercises
the pymongo-backed repository methods.
"""

from datetime import datetime, timedelta

import pytest

from tipi_data import DoesNotExist
from tipi_data.models.deputy import Deputy
from tipi_data.models.initiative import Initiative
from tipi_data.models.topic import Topic
from tipi_data.repositories.alerts import Alerts, InitiativeAlerts
from tipi_data.repositories.deputies import Deputies
from tipi_data.repositories.initiatives import Initiatives
from tipi_data.repositories.knowledgebases import KnowledgeBases
from tipi_data.repositories.scanned import Scanned
from tipi_data.repositories.tags import Tags
from tipi_data.repositories.topics import Topics
from tipi_data.repositories.votings import Votings


# ---- Topics / KnowledgeBases / Tags -------------------------------------------------

def test_topics_natsorted_and_kb(mongo_db):
    mongo_db.topics.insert_many([
        {"_id": "t10", "name": "Tema 10", "knowledgebase": "kb1", "public": True,
         "tags": [{"tag": "x", "subtopic": "s", "regex": "foo", "shuffle": False}]},
        {"_id": "t2", "name": "Tema 2", "knowledgebase": "kb1", "public": False,
         "tags": [{"tag": "y", "subtopic": "s2", "regex": "bar", "shuffle": False}]},
        {"_id": "t1", "name": "Tema 1", "knowledgebase": "kb2", "public": True, "tags": []},
    ])

    all_topics = Topics.get_all()
    assert all(isinstance(t, Topic) for t in all_topics)
    # natural sort: "Tema 2" before "Tema 10"
    names = [t.name for t in Topics.get_all_sorted()]
    assert names == ["Tema 1", "Tema 2", "Tema 10"]

    kb1 = Topics.by_kb("kb1")
    assert {t.id for t in kb1} == {"t10", "t2"}

    assert set(KnowledgeBases.get_all()) == {"kb1", "kb2"}
    assert KnowledgeBases.get_public() == ["kb1", "kb2"] or set(KnowledgeBases.get_public()) == {"kb1", "kb2"}
    assert set(Topics.get_subtopics()) >= {"s", "s2"}


def test_topics_get_raises_does_not_exist(mongo_db):
    with pytest.raises(DoesNotExist):
        Topics.get("nonexistent")


def test_tags_by_kb_compiles(mongo_db):
    mongo_db.topics.insert_one({
        "_id": "t1", "name": "Tema", "knowledgebase": "kb1", "public": True,
        "tags": [{"tag": "x", "subtopic": "s", "regex": "hola", "shuffle": False}],
    })
    tags = Tags.by_kb("kb1")
    assert len(tags) == 1
    assert tags[0]["topic"] == "Tema"
    assert tags[0]["compiletag"].search("HOLA")  # case-insensitive compiled regex


# ---- Deputies -----------------------------------------------------------------------

def test_deputies_counts_only_actives(mongo_db):
    mongo_db.deputies.insert_many([
        {"_id": "d1", "name": "A", "parliamentarygroup": "G", "active": True, "gender": "Mujer", "age": 30},
        {"_id": "d2", "name": "B", "parliamentarygroup": "G", "active": True, "gender": "Hombre", "age": 70},
        {"_id": "d3", "name": "C", "parliamentarygroup": "G", "active": False, "gender": "Mujer", "age": 40},
    ])
    assert Deputies.get_total("G") == 2          # inactive excluded
    assert Deputies.get_total_females("G") == 1  # d3 inactive
    assert Deputies.get_total_under_35("G") == 1
    assert Deputies.get_total_over_65("G") == 1
    assert all(isinstance(d, Deputy) for d in Deputies.get_all())


def test_deputies_birthdays(mongo_db):
    today = datetime.today()
    mongo_db.deputies.insert_many([
        {"_id": "b1", "name": "Birthday", "active": True,
         "birthdate": datetime(1980, today.month, today.day)},
        {"_id": "b2", "name": "NotToday", "active": True,
         "birthdate": datetime(1980, 1, 1) if today.month != 1 or today.day != 1
         else datetime(1980, 2, 2)},
    ])
    birthdays = Deputies.get_birthdays()
    ids = {d.id for d in birthdays}
    assert "b1" in ids
    assert "b2" not in ids


# ---- Initiatives --------------------------------------------------------------------

def test_initiatives_get_and_queries(mongo_db):
    mongo_db.initiatives.insert_many([
        {"_id": "i1", "title": "One", "reference": "R1", "tagged": [],
         "updated": datetime(2024, 1, 1)},
        {"_id": "i2", "title": "Two", "reference": "R1",
         "tagged": [{"knowledgebase": "kb", "topics": ["t"], "tags": []}],
         "updated": datetime(2024, 2, 1)},
    ])
    got = Initiatives.get("i1")
    assert isinstance(got, Initiative) and got.title == "One"

    with pytest.raises(DoesNotExist):
        Initiatives.get("missing")

    by_ref = Initiatives.by_reference("R1")
    # default ordering: -updated
    assert [i.id for i in by_ref] == ["i2", "i1"]

    untagged = Initiatives.get_all_untagged()
    assert {i.id for i in untagged} == {"i1"}

    assert {i.id for i in Initiatives.by_kb("kb")} == {"i2"}


# ---- Votings (write path) -----------------------------------------------------------

def test_votings_save_roundtrip(mongo_db):
    mongo_db.parliamentarygroups.insert_one(
        {"_id": "g1", "name": "Group One", "shortname": "G1"})

    data = {
        "informacion": {
            "textoExpediente": "Expediente",
            "textoSubGrupo": "Sub text",
            "tituloSubGrupo": "Sub title",
        },
        "totales": {"presentes": 1, "noVotan": 0, "afavor": 1, "enContra": 0, "abstenciones": 0},
        "votaciones": [
            {"diputado": "Dip", "asiento": "1", "grupo": "G1", "voto": "Sí"},
        ],
    }
    Votings.save("REF-1", data)

    stored = Votings.get_by("REF-1")
    assert len(stored) == 1
    voting = stored[0]
    assert voting.reference == "REF-1"
    assert voting.title == "Expediente"
    assert voting.totals.yes == 1
    g1 = next(g for g in voting.by_groups if g.name == "G1")
    assert g1.votes.yes == 1


# ---- Alerts -------------------------------------------------------------------------

def test_alerts_get_with_unvalidated_searches(mongo_db):
    mongo_db.alerts.insert_many([
        {"_id": "a1", "email": "all-validated@x.es",
         "searches": [{"hash": "h1", "validated": True}]},
        {"_id": "a2", "email": "some-unvalidated@x.es",
         "searches": [{"hash": "h2", "validated": False}]},
        {"_id": "a3", "email": "mixed@x.es",
         "searches": [{"hash": "h3", "validated": True},
                      {"hash": "h4", "validated": False}]},
    ])
    ids = {a.id for a in Alerts.get_with_unvalidated_searches()}
    assert ids == {"a2", "a3"}


def test_alerts_save_roundtrip(mongo_db):
    mongo_db.alerts.insert_one({
        "_id": "a1", "email": "save@x.es",
        "searches": [{"hash": "h1", "validated": False}]})

    alert = Alerts.get_with_unvalidated_searches()[0]
    alert.searches[0].validation_email_sent = True
    alert.searches[0].validation_email_sent_date = datetime(2024, 1, 1)
    Alerts.save(alert)

    stored = mongo_db.alerts.find_one({"_id": "a1"})
    assert stored["searches"][0]["validation_email_sent"] is True
    assert stored["searches"][0]["validation_email_sent_date"] == datetime(2024, 1, 1)


def test_alerts_remove_search_pulls_only_matching_hash(mongo_db):
    mongo_db.alerts.insert_one({
        "_id": "a1", "email": "pull@x.es",
        "searches": [{"hash": "h1", "validated": False},
                     {"hash": "h2", "validated": False}]})

    Alerts.remove_search("h1")

    stored = mongo_db.alerts.find_one({"_id": "a1"})
    assert [s["hash"] for s in stored["searches"]] == ["h2"]


def test_alerts_delete_empty(mongo_db):
    mongo_db.alerts.insert_many([
        {"_id": "empty", "email": "empty@x.es", "searches": []},
        {"_id": "full", "email": "full@x.es",
         "searches": [{"hash": "h1", "validated": True}]},
    ])
    Alerts.delete_empty()
    remaining = {d["_id"] for d in mongo_db.alerts.find()}
    assert remaining == {"full"}


def test_initiative_alerts_by_search_excludes_fields(mongo_db):
    mongo_db.initiatives_alerts.insert_one({
        "_id": "i1", "title": "Title", "content": ["secret body"],
        "tagged": [{"knowledgebase": "kb1", "topics": [], "tags": []}]})

    results = InitiativeAlerts.by_search({}, "kb1", exclude_fields=["content"])
    assert len(results) == 1
    assert "content" not in results[0].model_dump()
    assert results[0].title == "Title"


# ---- Scanned ------------------------------------------------------------------------

def test_scanned_delete_expired(mongo_db):
    now = datetime(2024, 6, 1)
    mongo_db.scanned.insert_many([
        {"_id": "past", "expiration": now - timedelta(days=1)},
        {"_id": "future", "expiration": now + timedelta(days=1)},
    ])
    Scanned.delete_expired(now)
    remaining = {d["_id"] for d in mongo_db.scanned.find()}
    assert remaining == {"future"}


def test_scanned_get_unverified_since(mongo_db):
    cutoff = datetime(2024, 6, 1)
    mongo_db.scanned.insert_many([
        {"_id": "recent-unverified", "created": cutoff + timedelta(days=1), "verified": False},
        {"_id": "recent-verified", "created": cutoff + timedelta(days=1), "verified": True},
        {"_id": "old-unverified", "created": cutoff - timedelta(days=1), "verified": False},
    ])
    ids = {s.id for s in Scanned.get_unverified_since(cutoff)}
    assert ids == {"recent-unverified"}
