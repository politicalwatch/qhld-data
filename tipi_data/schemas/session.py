"""Session (parliamentary sitting) output schema.

A sitting is returned as its metadata plus the roster of initiative ``references``
debated in it — never its speeches inline (a sitting hosts many, fetched separately
via the speeches endpoint filtered by ``session_id``). ``speeches_count`` is filled
on the detail view only.
"""

from tipi_data.schemas.base import BaseSchema


class SessionSchema(BaseSchema):
    id: str
    legislature: str | None = None
    session_link: str | None = None
    name: str | None = None
    code: str | None = None
    congress_session_id: str | None = None
    date: int | None = None
    video_link: str | None = None
    references: list[str] = []
    speeches_count: int | None = None

    @classmethod
    def from_doc(cls, obj, speeches_count=None):
        session = cls.model_validate(obj)
        session.speeches_count = speeches_count
        return session
