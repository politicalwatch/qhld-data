"""BSON round-trip parity: a model built from a stored document must reproduce
that document's keys/values when dumped (the data-shape invariant). ``to_bson``
may *add* empty-default keys (mongoengine did the same on re-save), so we assert
every original key/value is reproduced rather than strict equality."""

from datetime import datetime

import pytest
from bson import ObjectId
from pydantic import ValidationError

from tipi_data.models.alert import Alert, Search
from tipi_data.models.deputy import Deputy
from tipi_data.models.footprint import FootprintByTopic
from tipi_data.models.initiative import Initiative
from tipi_data.models.place import Place
from tipi_data.models.query_gap import UNRESOLVED, QueryGap, QueryGapEvent
from tipi_data.models.search_rating import SearchRating
from tipi_data.models.session import Session
from tipi_data.models.speech import Speech
from tipi_data.models.speech_alignment import SpeechAlignment, track_id
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
        "references": ["161/000123", "161/000124"],
        "video_id": "776209",
        "session_id": "sess-1",
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
        "speech": [
            # `langs` lists every language the block is in and always opens with `lang`;
            # the as-delivered block here also carries a Spanish quotation.
            {"lang": "gl", "text": "Grazas, señora presidenta.", "original": True,
             "partial": False, "langs": ["gl", "es"]},
            {"lang": "es", "text": "Gracias, señora presidenta.", "original": False,
             "partial": True, "langs": ["es"]},
        ],
        "original_language": "gl",
        "split_verdict": {"method": "acoustic", "fingerprint": "abc123"},
        "mentions": [
            {"person_id": "nunez-feijoo-alberto", "person_type": "deputy",
             "name": "Núñez Feijóo, Alberto", "surface_forms": ["Feijóo"], "count": 2},
            {"person_id": "isabel-diaz-ayuso", "person_type": "regional_president",
             "name": "Díaz Ayuso, Isabel", "surface_forms": ["Ayuso"], "count": 1},
        ],
        "entities": [
            {"key": "eurovision", "surface_forms": ["Eurovisión"], "count": 3},
            {"key": "guerra de gaza",
             "surface_forms": ["guerra de Gaza", "la guerra de Gaza"], "count": 2},
        ],
    }
    dumped = assert_reproduces(Speech, doc)
    assert dumped["_id"] == "sp-1"
    assert "id" not in dumped  # dumped by alias only
    assert dumped["mentions"][0]["person_type"] == "deputy"
    assert dumped["mentions"][1]["person_id"] == "isabel-diaz-ayuso"
    assert dumped["entities"][0]["key"] == "eurovision"
    # a rendering that covers only part of its original, and how the shape was decided
    assert dumped["speech"][1]["partial"] is True
    assert dumped["split_verdict"]["method"] == "acoustic"


def test_speech_without_entities_defaults_empty():
    # Corpus documents predating the entities field must validate cleanly.
    speech = Speech.model_validate({"_id": "sp-legacy"})
    assert speech.entities == []
    assert speech.mentions == []


def test_speech_alignment_roundtrip():
    doc = {
        "_id": "sp-1:gl",
        "speech_id": "sp-1",
        "lang": "gl",
        "block_index": 0,
        "original": True,
        "cues": [
            {"start_ms": 12013, "end_ms": 15136, "char_start": 0, "char_end": 26},
            {"start_ms": 16357, "end_ms": 21343, "char_start": 27, "char_end": 83},
        ],
        "text_sha256": "a" * 64,
        "text_length": 10411,
        "model_id": "onnx-community/mms-300m-1130-forced-aligner-ONNX",
        "model_revision": "2100fb247d8e",
        "model_sha256": "b" * 64,
        "score": 97.0,
        "verdict": "ok",
        "audio_seconds": 755.02,
        "created_at": datetime(2026, 8, 6, 21, 9, 0),
    }
    dumped = assert_reproduces(SpeechAlignment, doc)
    assert dumped["_id"] == "sp-1:gl"
    assert "id" not in dumped  # dumped by alias only
    assert dumped["cues"][1]["start_ms"] == 16357


def test_speech_alignment_defaults_are_insertable():
    alignment = SpeechAlignment(
        _id=track_id("sp-2", "es"), speech_id="sp-2", lang="es", block_index=0,
        text_sha256="c" * 64, text_length=9693)
    dumped = alignment.to_bson()
    assert dumped["_id"] == "sp-2:es"
    assert dumped["cues"] == []
    assert isinstance(dumped["created_at"], datetime)
    # A track is as-delivered unless it says otherwise: the plain case is a speech
    # given in Spanish, whose only block is the one that was spoken.
    assert dumped["original"] is True
    # Unscored until the trust gate has run; unset -> None -> excluded.
    assert "score" not in dumped
    assert "verdict" not in dumped


def test_a_speech_that_is_no_longer_undecided_asks_for_its_verdict_to_go():
    """``to_bson`` drops every ``None``, so a ``$set`` write alone can never take a
    field away. A speech says which of its fields mean something by being absent."""
    settled = Speech(_id="sp-4", speaker="Apellido, Nombre")
    assert "split_verdict" not in settled.to_bson()
    assert settled.to_unset() == ["split_verdict"]

    undecided = Speech(_id="sp-5", speaker="Apellido, Nombre",
                       split_verdict={"method": "undecided", "fingerprint": "abc123"})
    assert undecided.to_unset() == []


def test_a_model_declaring_nothing_clearable_asks_for_nothing():
    # The default, and why the sitting's own save can carry the same clause harmlessly.
    assert Session(_id="sess-1").to_unset() == []


def test_the_two_tracks_of_one_speech_get_distinct_keys():
    """The whole point of the composite key: a co-official speech carries an
    as-delivered track and a Spanish one, and neither may overwrite the other."""
    assert track_id("sp-3", "gl") != track_id("sp-3", "es")
    assert track_id("sp-3", "gl").startswith("sp-3")


def test_search_rating_roundtrip():
    doc = {
        "_id": ObjectId(),
        "rating": 2,
        "query": "intervenciones de Tesh Sidi sobre el Sáhara",
        "query_meta": {
            "semantic_query": "Sáhara",
            "filters": {},
            "browse": False,
            "unresolved": [
                {"field": "speaker", "value": "Tesh Sidi", "blocking": True,
                 "suggestion": "'Sidi Mohamed, Tesh' (61)"}
            ],
        },
        "reasons": ["persona_no_reconocida"],
        "comment": "No encuentra a esta diputada",
        "result_ids": ["sp-1", "sp-2"],
        "results_count": 2,
        "corpus": "2026-08-03T04:12:00",
        "created_at": datetime(2026, 8, 3, 9, 30, 0),
    }
    assert_reproduces(SearchRating, doc)


def test_search_rating_is_insertable_and_strict():
    rating = SearchRating(rating=5, query="vivienda")
    dumped = rating.to_bson()
    # A fresh rating has no _id, so Mongo assigns one on insert.
    assert "_id" not in dumped
    assert isinstance(dumped["created_at"], datetime)
    assert dumped["reasons"] == []
    assert "comment" not in dumped  # unset -> None -> excluded

    # extra="forbid": the payload comes from a public endpoint, so an unexpected
    # key must be rejected rather than silently persisted.
    with pytest.raises(ValidationError):
        SearchRating(rating=5, query="vivienda", injected="whatever")


def test_query_gap_roundtrip():
    doc = {
        "_id": ObjectId("665f1c2e4a1b2c3d4e5f6071"),
        "field": "mentions",
        "key": "rueda",
        "outcome": "unresolved",
        "surface_forms": ["Rueda", "señor Rueda"],
        "count": 14,
        "blocking_count": 12,
        "counts_by_month": {"2026-08": 12, "2026-09": 2},
        "suggestions": [None, "'Rueda Perelló, Patricia' (87)"],
        "chosen": [],
        "tied": [],
        "examples": [{
            "query": "qué ha dicho Rueda sobre la sanidad gallega",
            "semantic_query": "sanidad gallega",
            "filters": {},
            "value": "Rueda",
            "suggestion": "'Rueda Perelló, Patricia' (87)",
            "parser_model": "gpt-5.4-nano-2026-03-17",
            "at": datetime(2026, 9, 2, 11, 4, 0),
        }],
        "first_seen": datetime(2026, 8, 4, 9, 12, 0),
        "last_seen": datetime(2026, 9, 2, 11, 4, 0),
    }
    assert_reproduces(QueryGap, doc)


def test_query_gap_event_is_strict():
    event = QueryGapEvent(
        field="mentions", key="rueda", outcome=UNRESOLVED, value="Rueda",
        query="qué ha dicho Rueda")
    assert isinstance(event.at, datetime)
    assert event.tied == [] and event.suggestion is None

    # extra="forbid" here guards against OUR typos, not a hostile payload: the event is
    # assembled field by field at the call site, where a misspelled name would otherwise
    # be stored as a new field and noticed by nobody.
    with pytest.raises(ValidationError):
        QueryGapEvent(field="mentions", key="rueda", outcome=UNRESOLVED, value="Rueda",
                      query="x", sugestion="typo")


def test_session_roundtrip():
    doc = {
        "_id": "sess-1",
        "legislature": "15",
        "session_link": "/public_oficiales/L15/CONG/DS/PL/DSCD-15-PL-13.PDF",
        "name": "Pleno",
        "code": "DSCD-15-PL-13",
        "congress_session_id": "12",
        "date": 20231213,
        "video_link": "http://video/full-session.mp4",
        "references": ["172/000001", "172/000005"],
    }
    dumped = assert_reproduces(Session, doc)
    assert dumped["_id"] == "sess-1"
    assert "id" not in dumped  # dumped by alias only
