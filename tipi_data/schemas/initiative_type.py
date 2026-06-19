from tipi_data.schemas.base import BaseSchema


class InitiativeTypeSchema(BaseSchema):
    # NOTE: ``group`` was marshmallow ``load_only`` -> intentionally not exposed.
    id: str
    name: str | None = None
