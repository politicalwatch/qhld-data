"""Speech (intervention) output schemas (two variants).

- ``SpeechCompactSchema``:  list view — speaker/session metadata + mentions, **no text**
  (a listing of many speeches stays light).
- ``SpeechExtendedSchema``: detail view — the compact fields plus the full per-language
  ``speech`` text blocks.

``mentions`` is the list of people named within the speech (resolved to deputies or to
the non-deputy persons catalog); ``speech`` blocks carry the as-delivered original and
its Spanish translation for co-official-language interventions.
"""

from tipi_data.schemas.base import BaseSchema


class SpeechTextOut(BaseSchema):
    lang: str | None = None
    text: str | None = None
    original: bool | None = None


class MentionOut(BaseSchema):
    person_id: str | None = None
    person_type: str | None = None
    name: str | None = None
    surface_forms: list[str] = []
    count: int | None = None


class SpeechCompactSchema(BaseSchema):
    id: str
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
    original_language: str | None = None
    mentions: list[MentionOut] = []


class SpeechExtendedSchema(SpeechCompactSchema):
    speech: list[SpeechTextOut] = []
