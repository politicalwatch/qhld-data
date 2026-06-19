from datetime import datetime

from tipi_data.schemas.base import BaseSchema, TaggedOut


class ScannedSchema(BaseSchema):
    id: str
    title: str | None = None
    excerpt: str | None = None
    result: list[TaggedOut] = []
    created: datetime | None = None
    expiration: datetime | None = None
    verified: bool | None = None
