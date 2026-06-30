from tipi_data.models.base import MongoModel


class Session(MongoModel):
    """A parliamentary sitting (one Diario de Sesiones publication).

    A sitting hosts the debates of many initiatives, so it is the natural parent
    of the ``Speech`` documents that share its ``session_link`` (the speeches'
    ``session_id`` equals this document's ``_id``). ``references`` is the roster of
    initiatives debated in the sitting; the debate of a single initiative is the
    ``(session, reference)`` pairing, materialised by the speeches that share both.

    ``code`` is the canonical Diario document code (the PDF filename stem, e.g.
    ``DSCD-15-PL-13``: legislature 15, Pleno, sitting 13); ``congress_session_id``
    is the Congress API's internal ``idsesion`` (kept for debugging / updates).
    Metadata, including the full-sitting ``video_link``, comes from the Congress
    interventions API."""

    legislature: str | None = None
    session_link: str | None = None
    name: str | None = None
    code: str | None = None
    congress_session_id: str | None = None
    date: int | None = None
    video_link: str | None = None
    references: list[str] = []
