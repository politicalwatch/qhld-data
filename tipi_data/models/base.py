"""Pydantic v2 base models backing the pymongo data layer.

These replace the mongoengine ``Document`` / ``EmbeddedDocument`` hierarchy. The bases
map to the real shape differences in the data: ``_id`` type (string / ObjectId / none)
and whether the schema is fixed or flexible (``extra="allow"``). A small ``__getitem__``
/ ``__setitem__`` shim preserves the dict-style access (``doc['field']``) mongoengine
documents allowed and that consumers still rely on.

Subclasses set only the *delta* in ``model_config``; Pydantic v2 merges config across
inheritance.
"""

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


class DocBase(BaseModel):
    """Shared config + compatibility helpers for every document. Embedded documents
    (stored inline, no ``_id``) subclass this directly."""

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        arbitrary_types_allowed=True,
    )

    # mongoengine documents allowed both ``doc.field`` and ``doc['field']``.
    # Consumers (pinned to v1.x) use both; keep the dict-style access working.
    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def to_bson(self):
        """BSON-ready dict for writes. ``exclude_none`` keeps the document shape
        equivalent to mongoengine, which never stored unset fields (but did store
        explicit falsy values like ``0``, ``False``, ``[]``)."""
        return self.model_dump(by_alias=True, exclude_none=True)


class DynamicEmbeddedModel(DocBase):
    """Embedded document with a flexible schema (mongoengine DynamicEmbeddedDocument)."""

    model_config = ConfigDict(extra="allow")


class MongoModel(DocBase):
    """Top-level document stored with an explicit string ``_id``."""

    id: str = Field(alias="_id")


class DynamicModel(MongoModel):
    """Top-level document with a string ``_id`` and a flexible schema
    (mongoengine DynamicDocument with an explicit primary key)."""

    model_config = ConfigDict(extra="allow")


class ObjectIdModel(DocBase):
    """Top-level document with an auto-assigned ObjectId ``_id`` and a flexible
    schema (mongoengine DynamicDocument without an explicit primary key). ``id``
    is optional so new documents can be inserted and have Mongo assign the ``_id``."""

    model_config = ConfigDict(extra="allow")

    id: ObjectId | None = Field(default=None, alias="_id")
