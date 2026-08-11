from pydantic import BaseModel

from tipi_data.models.base import MongoModel


class SpeechText(BaseModel):
    """One block of a speech, identified by the role it plays rather than by where it
    sat in the document.

    A co-official-language speech is usually published in the Diario de Sesiones as the
    original (Galician/Catalan/Basque) followed by a Spanish rendering of it, and each
    becomes a block: ``original`` marks what was delivered, ``lang`` the ISO-639-1 code
    of the language it is mostly in. A speech delivered in one language — or in two,
    with no rendering published — has a single block, and that block may mix languages:
    the quotations a speaker reads aloud, a greeting, a passage they switch into.
    ``lang`` names the language the speech is *in*, not a guarantee about every sentence.

    ``partial`` marks a rendering that covers only part of the original. It is never set
    on an ``original`` block, which is complete by construction."""

    lang: str
    text: str
    original: bool
    partial: bool = False


class SplitVerdict(BaseModel):
    """How a speech's blocks were arrived at, when it was not simply read off the text.

    Absent on the ordinary speech, whose shape the text and the clip settle between them
    — the same convention ``SpeechText.partial`` follows. ``method`` is ``"undecided"``
    where the evidence did not settle it and the blocks are a provisional reading, or
    ``"acoustic"`` where the audio was consulted to break the tie.

    ``fingerprint`` is of the text the verdict was reached against. Extraction re-reads
    this rather than recomputing (deciding acoustically costs a video download), so the
    fingerprint is what stops a verdict outliving the text it describes: when they
    disagree the verdict is discarded and the speech is decided afresh."""

    method: str
    fingerprint: str


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


class NamedEntity(BaseModel):
    """A non-person named entity referenced within a speech — an organization
    ("Navantia"), an event ("Eurovisión"), a law ("ley de amnistía"), a conflict
    ("guerra de Gaza"), a place the speech talks about ("Sáhara Occidental")…
    Extracted by NER over the Spanish text block, like ``Mention``, but with no
    catalog to resolve against: the identity is the text itself.

    ``key`` is the canonical normalized form (lowercased, unaccented, leading
    articles stripped) — search filters match on it, so the same normalization
    must produce it at tagging time and at query time. ``surface_forms`` collects
    the distinct raw spans that normalized to this key ("la guerra de Gaza",
    "guerra de Gaza"); ``count`` is their total occurrences. The NER label
    (ORG/LOC/MISC) is deliberately not stored: the model assigns those too
    erratically to carry meaning."""

    key: str
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
    (``video_intervencion.id01``), empty until the sitting's video is published.

    ``duration`` is how many seconds that video runs, read from its container header.
    It is what makes the stored text checkable: a transcript should take roughly as
    long to say as its clip lasts, so text that could not physically have been spoken
    in the time available has been truncated, over-captured, or mis-split across
    languages. ``None`` where the video is unpublished or its header unreadable —
    never ``0``, which would read as an empty clip."""

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
    duration: float | None = None
    speech: list[SpeechText] = []
    original_language: str | None = None
    split_verdict: SplitVerdict | None = None
    mentions: list[Mention] = []
    interruptions: list[Interruption] = []
    entities: list[NamedEntity] = []
