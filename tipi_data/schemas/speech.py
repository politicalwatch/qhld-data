"""Speech (intervention) output schemas (two variants).

- ``SpeechCompactSchema``:  list view — speaker/session metadata + mentions, **no text**
  (a listing of many speeches stays light).
- ``SpeechExtendedSchema``: detail view — the compact fields plus the full per-language
  ``speech`` text blocks.

``mentions`` is the list of people named within the speech (resolved to deputies or to
the non-deputy persons catalog); ``interruptions`` the people who interjected from the
floor while it was delivered (each with the people THEY named); ``speech`` blocks carry
the as-delivered original and its Spanish translation for co-official-language
interventions; ``subtitles`` lists the languages the intervention's video has a timed
transcript for, one track per language.
"""

from tipi_data.schemas.base import BaseSchema


class SpeechTextOut(BaseSchema):
    lang: str | None = None
    text: str | None = None
    original: bool | None = None
    partial: bool = False


class MentionOut(BaseSchema):
    person_id: str | None = None
    person_type: str | None = None
    name: str | None = None
    surface_forms: list[str] = []
    count: int | None = None


class InterruptionOut(BaseSchema):
    person_id: str | None = None
    person_type: str | None = None
    name: str | None = None
    surface_forms: list[str] = []
    count: int | None = None
    quotes: list[str] = []
    reactions: list[str] = []
    mentions: list[MentionOut] = []


class SubtitleTrackOut(BaseSchema):
    """That a speech has subtitles in one language.

    Only whether a track can be fetched, never the cues: the track itself is a
    separate request the player makes, and most speeches have none, so a detail
    response says which language to label it with and stops there.

    ``original`` distinguishes the track timed against the words actually spoken from
    the one timed against their Spanish translation. Both are real timings measured
    against the same audio, but a reader deserves to be told which they are watching.
    """

    lang: str | None = None
    original: bool = True


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
    interruptions: list[InterruptionOut] = []


class SpeechExtendedSchema(SpeechCompactSchema):
    speech: list[SpeechTextOut] = []
    # Filled in by the caller, not by the speech document: alignments live in
    # their own collection. A list because a co-official-language intervention is
    # subtitled twice, in the language it was delivered in and in Spanish; empty
    # whenever no track is usable — see ``repositories.speech_alignments``.
    subtitles: list[SubtitleTrackOut] = []
