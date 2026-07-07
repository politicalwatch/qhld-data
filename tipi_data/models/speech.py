from pydantic import BaseModel

from tipi_data.models.base import MongoModel


class SpeechText(BaseModel):
    """A single-language block of a speech.

    Co-official-language speeches are published in the Diario de Sesiones as the
    full original (Galician/Catalan/Basque) followed by its full Spanish
    translations. We store each language as its own block: ``original`` marks the
    as-delivered block, ``lang`` is the detected ISO-639-1 code. Monolingual
    speeches have a single block (``original=True``)."""

    lang: str
    text: str
    original: bool


class Mention(BaseModel):
    """A person named *within* a speech (not the speaker). Extracted at index time
    by NER over the Spanish text block and resolved against a catalog of people.

    ``person_id`` is the canonical id of the resolved person: a ``Deputy._id`` slug
    for a sitting deputy, or the id of a non-deputy in the persons catalog (a
    government minister, the King, a regional president, a foreign leader…).
    ``person_type`` records which kind — ``"deputy"`` for deputies, otherwise
    ``"minister"``/``"former_pm"``/``"regional_president"``/``"foreign_leader"``/
    ``"head_of_state"``/``"official"``. ``surface_forms`` collects the distinct raw
    spans that resolved to this person (e.g. ``"Sánchez"``, ``"Pedro Sánchez"``);
    ``count`` is their total occurrences."""

    person_id: str | None = None
    person_type: str | None = None
    name: str
    surface_forms: list[str] = []
    count: int = 0


class Speech(MongoModel):
    reference: str | None = None
    session_id: str | None = None
    speaker: str | None = None
    speaker_surname: str | None = None
    group: str | None = None
    role: str | None = None
    order: int | None = None
    legislature: str | None = None
    date: int | None = None
    session_name: str | None = None
    video_link: str | None = None
    session_link: str | None = None
    speech: list[SpeechText] = []
    original_language: str | None = None
    mentions: list[Mention] = []
