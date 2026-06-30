from tipi_data.models.base import MongoModel


class Speech(MongoModel):
    reference: str | None = None
    speaker: str | None = None
    speaker_surname: str | None = None
    group: str | None = None
    order: int | None = None
    legislature: str | None = None
    date: int | None = None
    session_name: str | None = None
    video_link: str | None = None
    session_link: str | None = None
    speech: str | None = None
