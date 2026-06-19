from tipi_data.schemas.base import BaseSchema


class TopicSchema(BaseSchema):
    # marshmallow load_only -> excluded: description, tags, public
    id: str
    name: str | None = None
    shortname: str | None = None
    knowledgebase: str | None = None


class TopicTagOut(BaseSchema):
    """Subset emitted by the old ``TagsField`` (only subtopic + tag)."""

    subtopic: str | None = None
    tag: str | None = None


class TopicExtendedSchema(BaseSchema):
    # marshmallow load_only -> excluded: public
    id: str
    name: str | None = None
    shortname: str | None = None
    description: list[str] = []
    tags: list[TopicTagOut] = []
    knowledgebase: str | None = None
