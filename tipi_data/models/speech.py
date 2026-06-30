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
