from tipi_data.models.base import MongoModel


class Video(MongoModel):
    reference: str | None = None
    link: str | None = None
    session_name: str | None = None
    speaker: str | None = None
    type: str | None = None
    date: int | None = None
