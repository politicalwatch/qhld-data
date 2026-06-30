"""BSON round-trip parity: a model built from a stored document must reproduce
that document's keys/values when dumped (the data-shape invariant). ``to_bson``
may *add* empty-default keys (mongoengine did the same on re-save), so we assert
every original key/value is reproduced rather than strict equality."""

from datetime import datetime

import pytest
from bson import ObjectId

from tipi_data.models.alert import Alert, Search
from tipi_data.models.deputy import Deputy
from tipi_data.models.footprint import FootprintByTopic
from tipi_data.models.initiative import Initiative
from tipi_data.models.place import Place
from tipi_data.models.speech import Speech
from tipi_data.models.stats import Stats
from tipi_data.models.voting import Voting

pytestmark = pytest.mark.unit


def assert_reproduces(model_cls, doc):
    """model_validate(doc).to_bson() reproduces every key/value in doc."""
    dumped = model_cls.model_validate(doc).to_bson()
    for key, value in doc.items():
        assert key in dumped, f"{model_cls.__name__}: missing key {key!r}"
        assert dumped[key] == value, f"{model_cls.__name__}: {key!r} {dumped[key]!r} != {value!r}"
    return dumped


def test_string_id_alias_roundtrip():
    doc = {"_id": "place-1", "name": "Madrid"}
    dumped = assert_reproduces(Place, doc)
    place = Place.model_validate(doc)
    assert place.id == "place-1"
    assert dumped["_id"] == "place-1"
    assert "id" not in dumped  # dumped by alias only


def test_dict_and_attribute_access():
    place = Place.model_validate({"_id": "p", "name": "X"})
    assert place.name == "X"
    assert place["name"] == "X"           # __getitem__ shim
    place["name"] = "Y"                   # __setitem__ shim
    assert place.name == "Y"
    assert place.get("missing", "def") == "def"


def test_membership_matches_mongoengine_semantics():
    # Regression: without __contains__, `in` falls back to Pydantic's __iter__
    # (which yields (name, value) pairs), so EVERY `'field' in doc` check
    # silently returned False. That made the spain extractor skip every existing
    # initiative and regenerate the whole corpus (61k refs) instead of the
    # daily delta. mongoengine's __contains__ was `getattr(...) is not None`.
    init = Initiative.model_validate(
        {"_id": "init-1", "reference": "161/000123", "status": "open"}
    )
    assert "reference" in init            # present, non-None -> True
    assert ("reference" not in init) is False  # the exact check the extractor runs
    assert "status" in init
    assert "title" not in init            # declared but unset (None) -> False
    assert "nope" not in init             # undeclared name -> False


def test_membership_keeps_falsy_non_none_values():
    # A present-but-falsy value is still "in" the document (mongoengine parity):
    # only None/absent counts as missing.
    init = Initiative.model_validate(
        {"_id": "i", "reference": "1/000001", "content": [], "author_deputies": []}
    )
    assert "content" in init              # [] is not None -> True
    assert "author_deputies" in init


def test_construct_by_field_name():
    # populate_by_name lets code construct with `id=` instead of `_id`
    place = Place(id="p2", name="N")
    assert place.to_bson()["_id"] == "p2"


def test_initiative_nested_roundtrip():
    doc = {
        "_id": "init-1",
        "title": "T",
        "reference": "REF",
        "author_deputies": ["a", "b"],
        "author_parliamentarygroups": [],
        "created": datetime(2024, 1, 2, 3, 4, 5),
        "updated": datetime(2024, 6, 7, 8, 9, 10),
        "status": "open",
        "tagged": [
            {
                "knowledgebase": "kb1",
                "topics": ["t1"],
                "topic_alignment": [{"topic": "t1", "percentage": 50.0}],
                "tags": [{"topic": "t1", "subtopic": "s", "tag": "x", "times": 3}],
            }
        ],
        "content": ["line1", "line2"],
        "extra": {"foo": "bar", "n": 1},
    }
    assert_reproduces(Initiative, doc)


def test_exclude_none_but_keep_falsy():
    # Unset (None) fields are dropped; explicit falsy values are kept.
    doc = {"_id": "d", "active": False, "age": 0, "public_position": []}
    dumped = Deputy.model_validate(doc).to_bson()
    assert dumped["active"] is False
    assert dumped["age"] == 0
    assert dumped["public_position"] == []
    assert "gender" not in dumped  # was never set -> None -> excluded


def test_dynamic_model_preserves_extra_fields():
    # Voting is dynamic: undeclared keys must round-trip.
    doc = {
        "_id": "v1",
        "reference": "R",
        "totals": {"present": 350, "yes": 200, "no": 100, "abstention": 50, "skip": 0},
        "by_groups": [{"name": "G", "votes": {"yes": 1, "no": 0, "abstention": 0, "skip": 0}}],
        "undeclared_field": {"nested": True},
    }
    dumped = assert_reproduces(Voting, doc)
    assert dumped["undeclared_field"] == {"nested": True}


def test_objectid_model_read_and_insert():
    oid = ObjectId()
    stats = Stats.model_validate({"_id": oid, "anything": 42})
    assert stats.id == oid
    assert stats.to_bson()["_id"] == oid
    assert stats.to_bson()["anything"] == 42
    # A fresh document has no _id, so Mongo will assign one on insert.
    assert "_id" not in Stats().to_bson()


def test_search_dynamic_embedded_roundtrip():
    doc = {"_id": "al-1", "email": "x@y.z", "searches": [
        {"hash": "h", "search": "s", "validated": True, "custom": "kept"}
    ]}
    dumped = Alert.model_validate(doc).to_bson()
    assert dumped["searches"][0]["validated"] is True
    assert dumped["searches"][0]["custom"] == "kept"  # dynamic embedded extra


def test_footprint_computed_at_is_per_instance():
    # Regression for the mongoengine default=datetime.now() (evaluated once at
    # import) bug -> default_factory now runs per instance.
    fp = FootprintByTopic(id="f1", name="topic")
    assert isinstance(fp.computed_at, datetime)


def test_speech_roundtrip():
    doc = {
        "_id": "sp-1",
        "reference": "161/000123",
        "speaker": "Apellido, Nombre",
        "speaker_surname": "Apellido",
        "group": "Grupo Parlamentario",
        "role": "Diputado",
        "order": 3,
        "legislature": "15",
        "date": 20240115,
        "session_name": "Sesión plenaria",
        "video_link": "http://video/x.mp4",
        "session_link": "/public_oficiales/L15/CONG-1",
        "speech": "Señorías, ...",
    }
    dumped = assert_reproduces(Speech, doc)
    assert dumped["_id"] == "sp-1"
    assert "id" not in dumped  # dumped by alias only
