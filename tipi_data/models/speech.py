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


class Interruption(BaseModel):
    """Someone interjecting from the floor while this speech is delivered, as
    recorded by the stenographers in a parenthesized annotation of the Diario de
    Sesiones — e.g. ``(El señor Núñez Feijóo: ¡Qué disparate!)``. Not part of what
    the speaker said, so kept apart from ``Speech.mentions``.

    ``person_id``/``person_type``/``name`` identify the interrupter as in
    ``Mention``; an unidentified interrupter (``Un señor diputado``, ``Varios
    señores diputados``…) has ``person_id=None`` and ``name`` set to the
    transcript's own label. ``surface_forms`` collects the distinct ways the
    transcript introduced them and ``count`` their total interjections here.

    Each interjection is either verbal — its transcription joins ``quotes`` — or a
    recorded reaction: ``reactions`` keeps the stenographer's description ("Risas",
    "hace signos negativos", "pronuncia palabras que no se perciben"). Only floor
    activity notable enough to be minuted lands in the Diario at all, so these
    also serve as a disruption signal. ``mentions`` are the people THEY named
    while interrupting (``(… Tellado Filgueira: Ábalos. Cerdán en la cárcel…)``
    yields mentions of Ábalos and Cerdán here)."""

    person_id: str | None = None
    person_type: str | None = None
    name: str
    surface_forms: list[str] = []
    count: int = 0
    quotes: list[str] = []
    reactions: list[str] = []
    mentions: list[Mention] = []


class Speech(MongoModel):
    """One physical intervention in a sitting.

    When several initiatives are debated jointly (an accumulated debate), the same
    intervention belongs to every one of them: ``references`` lists all the
    initiative references it addresses, accumulated across per-reference extraction
    runs (see ``Speeches.save``). ``video_id`` is the Congress intervention id
    (``video_intervencion.id01``), empty until the sitting's video is published."""

    references: list[str] = []
    video_id: str | None = None
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
    interruptions: list[Interruption] = []
