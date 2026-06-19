from tipi_data.schemas.base import BaseSchema


class VideoSchema(BaseSchema):
    id: str
    reference: str | None = None
    link: str | None = None
    session_name: str | None = None
    speaker: str | None = None
    type: str | None = None
    date: int | None = None
