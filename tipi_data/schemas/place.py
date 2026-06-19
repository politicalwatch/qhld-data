from tipi_data.schemas.base import BaseSchema


class PlaceSchema(BaseSchema):
    id: str
    name: str | None = None
