"""Repository integration tests against a real MongoDB (skipped if none reachable).

Each test seeds the collections it needs via the ``mongo_db`` fixture, then exercises
the pymongo-backed repository methods.
"""

from datetime import datetime, timedelta

import pytest

from tipi_data import DoesNotExist
from tipi_data.models.amendment import Amendment
from tipi_data.models.deputy import Deputy
from tipi_data.models.footprint import (
    FootprintByDeputy,
    FootprintByParliamentaryGroup,
    FootprintByTopic,
    FootprintElement,
)
from tipi_data.models.initiative import Initiative
from tipi_data.models.parliamentarygroup import ParliamentaryGroup
from tipi_data.models.place import Place
from tipi_data.models.stats import Stats as StatsModel
from tipi_data.models.topic import Topic
from tipi_data.models.video import Video
from tipi_data.repositories.alerts import Alerts, InitiativeAlerts
from tipi_data.repositories.amendments import Amendments
from tipi_data.repositories.deputies import Deputies
from tipi_data.repositories.footprints import Footprints
from tipi_data.repositories.initiatives import Initiatives
from tipi_data.repositories.initiativetypes import InitiativeTypes
from tipi_data.repositories.knowledgebases import KnowledgeBases
from tipi_data.repositories.parliamentarygroups import ParliamentaryGroups
from tipi_data.repositories.places import Places
from tipi_data.repositories.scanned import Scanned
from tipi_data.repositories.stats import Stats
from tipi_data.repositories.tags import Tags
from tipi_data.repositories.topics import Topics
from tipi_data.repositories.videos import Videos
from tipi_data.repositories.votings import Votings

pytestmark = pytest.mark.integration


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


# ---- Amendments (collection is the singular "amendment") ----------------------------

def test_amendments_queries(mongo_db):
    mongo_db.amendment.insert_many([
        {"_id": "a1", "reference": "R1", "bulletin_name": "BOCG-1",
         "justification_tagged": [], "propossed_change_tagged": []},
        {"_id": "a2", "reference": "R1", "bulletin_name": "BOCG-2",
         "justification_tagged": [{"knowledgebase": "kb", "topics": ["t"], "tags": []}],
         "propossed_change_tagged": [{"knowledgebase": "kb", "topics": ["t"], "tags": []}]},
        {"_id": "a3", "reference": "R2", "bulletin_name": "BOCG-1",
         "justification_tagged": [{"knowledgebase": "kb", "topics": ["t"], "tags": []}],
         "propossed_change_tagged": []},
    ])

    by_ref = Amendments.by_reference("R1")
    assert all(isinstance(a, Amendment) for a in by_ref)
    assert {a.id for a in by_ref} == {"a1", "a2"}

    assert {a.id for a in Amendments.by_reference_and_bulletin("R1", "BOCG-1")} == {"a1"}

    # untagged = either tagged array empty/missing; a2 is fully tagged so excluded
    assert {a.id for a in Amendments.get_all_untagged()} == {"a1", "a3"}

    assert {a.id for a in Amendments.by_query({"reference": "R2"})} == {"a3"}


def test_amendments_save_roundtrip(mongo_db):
    amendment = Amendment(_id="R9/hash/1", reference="R9", bulletin_name="BOCG-9",
                          type="Enmienda")
    Amendments.save(amendment)

    # written to the singular "amendment" collection and readable back
    assert "amendment" in mongo_db.list_collection_names()
    stored = Amendments.by_reference("R9")
    assert len(stored) == 1 and stored[0].id == "R9/hash/1"
    assert stored[0].type == "Enmienda"


# ---- Footprints ---------------------------------------------------------------------

def test_footprints_topics(mongo_db):
    fp = FootprintByTopic(_id="t1", name="Tema",
                          deputies=[FootprintElement(name="d1", score=5.0)],
                          parliamentarygroups=[FootprintElement(name="g1", score=2.0)])
    Footprints.save_topic(fp)

    got = Footprints.get_by_topic("Tema")
    assert isinstance(got, FootprintByTopic) and got.id == "t1"
    assert got.deputies[0].name == "d1"
    assert {f.id for f in Footprints.get_all_topics()} == {"t1"}

    with pytest.raises(DoesNotExist):
        Footprints.get_by_topic("missing")


def test_footprints_deputies(mongo_db):
    Footprints.save_deputy(FootprintByDeputy(_id="d1", name="Dip One", score=4.0))
    Footprints.save_deputy(FootprintByDeputy(_id="d2", name="Dip Two", score=1.0))

    assert Footprints.get_by_deputy("Dip One").id == "d1"
    assert {f.id for f in Footprints.get_all_deputies()} == {"d1", "d2"}

    with pytest.raises(DoesNotExist):
        Footprints.get_by_deputy("missing")

    # id-keyed getters: hit returns the model, miss returns None (not raise)
    assert Footprints.get_by_deputy_id("d1").name == "Dip One"
    assert Footprints.get_by_deputy_id("missing") is None

    # batch getter returns a dict keyed by id, ignoring unknown ids
    batch = Footprints.get_by_deputy_ids(["d1", "d2", "missing"])
    assert set(batch) == {"d1", "d2"}
    assert batch["d2"].name == "Dip Two"


def test_footprints_parliamentarygroups(mongo_db):
    Footprints.save_parliamentarygroup(
        FootprintByParliamentaryGroup(_id="g1", name="Group One", score=3.0))

    assert Footprints.get_by_parliamentarygroup("Group One").id == "g1"
    assert {f.id for f in Footprints.get_all_parliamentarygroups()} == {"g1"}

    with pytest.raises(DoesNotExist):
        Footprints.get_by_parliamentarygroup("missing")

    assert Footprints.get_by_parliamentarygroup_id("g1").name == "Group One"
    assert Footprints.get_by_parliamentarygroup_id("missing") is None

    batch = Footprints.get_by_parliamentarygroup_ids(["g1", "missing"])
    assert set(batch) == {"g1"}


def test_footprints_get_range_by_all_topics(mongo_db):
    mongo_db.footprint_by_topics.insert_one({
        "_id": "t1", "name": "Tema",
        "deputies": [{"name": "d1", "score": 5}, {"name": "d2", "score": 3},
                     {"name": "d3", "score": 0}],
        "parliamentarygroups": [{"name": "g1", "score": 8}, {"name": "g2", "score": 2}],
    })

    result = Footprints.get_range_by_all_topics()
    assert len(result) == 1
    row = result[0]
    assert row["name"] == "Tema"
    # max = highest score; min = lowest score strictly greater than 0
    assert row["deputy"]["max"]["name"] == "d1"
    assert row["deputy"]["min"]["name"] == "d2"
    assert row["parliamentarygroup"]["max"]["name"] == "g1"
    assert row["parliamentarygroup"]["min"]["name"] == "g2"


def test_footprints_aggregate_deputies(mongo_db):
    Footprints.save_deputy(FootprintByDeputy(_id="d1", name="One", score=4.0))
    Footprints.save_deputy(FootprintByDeputy(_id="d2", name="Two", score=6.0))

    result = Footprints.aggregate_deputies(
        [{"$group": {"_id": None, "total": {"$sum": "$score"}}}])
    assert result[0]["total"] == 10


# ---- InitiativeTypes (collection "initiative_types") --------------------------------

def test_initiativetypes_queries(mongo_db):
    mongo_db.initiative_types.insert_many([
        {"_id": "it1", "name": "Pregunta", "group": "control"},
        {"_id": "it2", "name": "Anuncio", "group": "control"},
        {"_id": "it3", "name": "Ley", "group": "legislativo"},
    ])

    names = [t.name for t in InitiativeTypes.get_all()]
    assert names == ["Anuncio", "Ley", "Pregunta"]  # sorted by name

    assert InitiativeTypes.get_by_name("Ley").id == "it3"
    with pytest.raises(DoesNotExist):
        InitiativeTypes.get_by_name("missing")

    assert set(InitiativeTypes.get_names_by_group("control")) == {"Pregunta", "Anuncio"}


# ---- KnowledgeBases (distinct over topics; complements the topics test) -------------

def test_knowledgebases_all_and_public(mongo_db):
    mongo_db.topics.insert_many([
        {"_id": "t1", "name": "A", "knowledgebase": "kb1", "public": True, "tags": []},
        {"_id": "t2", "name": "B", "knowledgebase": "kb2", "public": False, "tags": []},
    ])
    assert set(KnowledgeBases.get_all()) == {"kb1", "kb2"}
    assert set(KnowledgeBases.get_public()) == {"kb1"}


# ---- ParliamentaryGroups ------------------------------------------------------------

def test_parliamentarygroups_get_and_sort(mongo_db):
    mongo_db.parliamentarygroups.insert_many([
        {"_id": "g1", "name": "Group One", "shortname": "G1",
         "composition": {"deputies": 5}},
        {"_id": "g2", "name": "Group Two", "shortname": "G2",
         "composition": {"deputies": 10}},
    ])

    # sorted by composition.deputies descending
    assert [g.id for g in ParliamentaryGroups.get_all()] == ["g2", "g1"]
    assert all(isinstance(g, ParliamentaryGroup) for g in ParliamentaryGroups.get_all())

    assert ParliamentaryGroups.get("g1").name == "Group One"
    with pytest.raises(DoesNotExist):
        ParliamentaryGroups.get("missing")

    assert ParliamentaryGroups.get_by_name("Group Two").id == "g2"
    with pytest.raises(DoesNotExist):
        ParliamentaryGroups.get_by_name("missing")

    # get_by_shortname returns None (not raise) when absent
    assert ParliamentaryGroups.get_by_shortname("G1").id == "g1"
    assert ParliamentaryGroups.get_by_shortname("missing") is None

    assert {g.id for g in ParliamentaryGroups.get_by_query({"shortname": "G2"})} == {"g2"}


def test_parliamentarygroups_save_roundtrip(mongo_db):
    ParliamentaryGroups.save(
        ParliamentaryGroup(_id="g9", name="Saved", shortname="S9",
                           parties=["P1", "P2"]))
    stored = mongo_db.parliamentarygroups.find_one({"_id": "g9"})
    assert stored["name"] == "Saved"
    assert stored["parties"] == ["P1", "P2"]


def test_parliamentarygroups_get_composition(mongo_db):
    mongo_db.deputies.insert_many([
        {"_id": "p1", "name": "A", "parliamentarygroup": "G", "active": True,
         "gender": "Mujer", "age": 30},
        {"_id": "p2", "name": "B", "parliamentarygroup": "G", "active": True,
         "gender": "Hombre", "age": 70},
        {"_id": "p3", "name": "C", "parliamentarygroup": "G", "active": False,
         "gender": "Mujer", "age": 40},
    ])

    composition = ParliamentaryGroups.get_composition("G")
    assert composition.deputies == 2  # inactive p3 excluded
    assert composition.gender.female == 1 and composition.gender.male == 1
    assert composition.ages.under35 == 1 and composition.ages.over65 == 1


# ---- Places -------------------------------------------------------------------------

def test_places_get_all_sorted(mongo_db):
    mongo_db.places.insert_many([
        {"_id": "pl2", "name": "Madrid"},
        {"_id": "pl1", "name": "Barcelona"},
    ])
    places = Places.get_all()
    assert all(isinstance(p, Place) for p in places)
    assert [p.name for p in places] == ["Barcelona", "Madrid"]  # sorted by name


# ---- Stats (singleton in collection "statistics") ----------------------------------

def test_stats_save_get_and_delete(mongo_db):
    with pytest.raises(DoesNotExist):
        Stats.get()  # empty

    Stats.save(StatsModel(total_initiatives=42))
    got = Stats.get()
    assert isinstance(got, StatsModel)
    assert got["total_initiatives"] == 42  # dynamic field preserved

    Stats.delete_all()
    with pytest.raises(DoesNotExist):
        Stats.get()


# ---- Videos -------------------------------------------------------------------------

def test_videos_save_roundtrip_and_upsert(mongo_db):
    Videos.save(Video(_id="v1", reference="R1", link="http://old", date=20240101))
    stored = mongo_db.videos.find_one({"_id": "v1"})
    assert stored["link"] == "http://old"

    # save again with the same id updates in place (upsert), not duplicates
    Videos.save(Video(_id="v1", reference="R1", link="http://new", date=20240101))
    assert mongo_db.videos.count_documents({}) == 1
    assert mongo_db.videos.find_one({"_id": "v1"})["link"] == "http://new"
