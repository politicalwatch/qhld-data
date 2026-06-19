"""Pydantic v2 base + shared embedded output models.

These replace the previous marshmallow-mongoengine schemas. They are presentation
(output) models consumed by qhld-backend only. Each model is built from a mongoengine
document via ``model_validate(doc)`` (``from_attributes=True``) or an explicit
``from_doc(...)`` classmethod when extra context (e.g. a knowledgebase filter) or
computed fields are involved.

None-valued fields are dropped at the API boundary via FastAPI
``response_model_exclude_none=True`` (the equivalent of marshmallow's
``model_skip_values=[None]``).
"""

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TagOut(BaseSchema):
    """Mirror of initiative ``Tag.serialize()``."""

    topic: str | None = None
    subtopic: str | None = None
    tag: str | None = None
    times: int | None = None


class TopicAlignmentOut(BaseSchema):
    """Mirror of ``TopicAlignment.serialize()``."""

    topic: str | None = None
    percentage: float | None = None


class TaggedOut(BaseSchema):
    """Mirror of ``Tagged.serialize()`` (used by Initiative + Scanned)."""

    knowledgebase: str | None = None
    topics: list[str] = []
    topic_alignment: list[TopicAlignmentOut] = []
    tags: list[TagOut] = []


class FootprintElementOut(BaseSchema):
    name: str | None = None
    score: float | None = None
