"""Tier-1 (no Mongo) tests for the browse output schemas.

Built straight from model instances via ``from_attributes``. Pin the compact-vs-extended
split (list omits the heavy text; detail includes it) and the session ``speeches_count``
being filled on detail only.
"""

from tipi_data.models.session import Session
from tipi_data.models.speech import Speech
from tipi_data.schemas.session import SessionSchema
from tipi_data.schemas.speech import SpeechCompactSchema, SpeechExtendedSchema


def _speech():
    return Speech(
        _id="sp-1",
        references=["172/000001", "172/000005"],
        session_id="sess-1",
        speaker="Montero Cuadrado, María Jesús",
        speaker_surname="Montero",
        group="GS",
        role="Vicepresidenta primera",
        order=3,
        legislature="15",
        date=20231213,
        session_name="Pleno",
        speech=[
            {"lang": "gl", "text": "Grazas.", "original": True},
            {"lang": "es", "text": "Gracias.", "original": False},
        ],
        original_language="gl",
        mentions=[
            {"person_id": "nunez-feijoo-alberto", "person_type": "deputy",
             "name": "Núñez Feijóo, Alberto", "surface_forms": ["Feijóo"], "count": 2},
        ],
    )


def test_speech_compact_omits_text_keeps_metadata_and_mentions():
    compact = SpeechCompactSchema.model_validate(_speech())
    dumped = compact.model_dump()
    assert "speech" not in dumped
    assert dumped["speaker"] == "Montero Cuadrado, María Jesús"
    assert dumped["references"] == ["172/000001", "172/000005"]
    assert dumped["mentions"][0]["person_id"] == "nunez-feijoo-alberto"


def test_speech_extended_includes_text_blocks():
    extended = SpeechExtendedSchema.model_validate(_speech())
    dumped = extended.model_dump()
    assert [b["lang"] for b in dumped["speech"]] == ["gl", "es"]
    assert dumped["speech"][1]["original"] is False
    # still carries the compact fields
    assert dumped["session_id"] == "sess-1"


def test_session_schema_count_filled_on_detail_only():
    session = Session(
        _id="sess-1", legislature="15", name="Pleno", code="DSCD-15-PL-13",
        date=20231213, references=["172/000001", "172/000005"],
    )
    listed = SessionSchema.from_doc(session)
    assert listed.speeches_count is None
    assert listed.references == ["172/000001", "172/000005"]

    detail = SessionSchema.from_doc(session, speeches_count=7)
    assert detail.speeches_count == 7
