from datetime import datetime

from tipi_data.schemas.base import BaseSchema, FootprintElementOut


class FootprintByTopicSchema(BaseSchema):
    id: str
    name: str | None = None
    deputies: list[FootprintElementOut] = []
    parliamentarygroups: list[FootprintElementOut] = []
    computed_at: datetime | None = None


class FootprintByDeputySchema(BaseSchema):
    id: str
    name: str | None = None
    score: float | None = None
    topics: list[FootprintElementOut] = []
    computed_at: datetime | None = None


class FootprintByParliamentaryGroupSchema(BaseSchema):
    id: str
    name: str | None = None
    score: float | None = None
    topics: list[FootprintElementOut] = []
    computed_at: datetime | None = None
