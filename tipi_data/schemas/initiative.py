"""Initiative output schemas (three variants).

Field-set differences preserved from the old marshmallow schemas:
- InitiativeSchema (``simple``):       no content / history / extra; ``place`` falls back to "".
- InitiativeNoContentSchema:           has history + extra; no content; plain ``place``.
- InitiativeExtendedSchema (``full``): has history + extra; ``content`` joined with newlines.

``authors``/``deputies`` are derived from the load-only author fields; ``tagged`` is
filtered by the knowledgebase(s) ``kb`` (a list or, preserving an existing quirk, a bare
string -> substring match). Build via ``from_doc(doc, kb)``.
"""

from datetime import datetime

from tipi_data.schemas.base import BaseSchema, TaggedOut


def _authors(obj):
    return list(obj.author_others or []) + list(obj.author_parliamentarygroups or [])


def _tagged(obj, kb):
    return [TaggedOut.model_validate(t) for t in obj.tagged if t.knowledgebase in kb]


class InitiativeSchema(BaseSchema):
    id: str
    title: str | None = None
    reference: str | None = None
    initiative_type: str | None = None
    initiative_type_alt: str | None = None
    created: datetime | None = None
    updated: datetime | None = None
    status: str | None = None
    url: str | None = None
    authors: list[str] = []
    deputies: list[str] = []
    place: str = ""
    tagged: list[TaggedOut] = []

    @classmethod
    def from_doc(cls, obj, kb):
        return cls(
            id=obj.id,
            title=obj.title,
            reference=obj.reference,
            initiative_type=obj.initiative_type,
            initiative_type_alt=obj.initiative_type_alt,
            created=obj.created,
            updated=obj.updated,
            status=obj.status,
            url=obj.url,
            authors=_authors(obj),
            deputies=list(obj.author_deputies or []),
            place=obj.place or "",
            tagged=_tagged(obj, kb),
        )


class InitiativeNoContentSchema(BaseSchema):
    id: str
    title: str | None = None
    reference: str | None = None
    initiative_type: str | None = None
    initiative_type_alt: str | None = None
    place: str | None = None
    created: datetime | None = None
    updated: datetime | None = None
    history: list[str] = []
    status: str | None = None
    url: str | None = None
    extra: dict | None = None
    authors: list[str] = []
    deputies: list[str] = []
    tagged: list[TaggedOut] = []

    @classmethod
    def from_doc(cls, obj, kb):
        return cls(
            id=obj.id,
            title=obj.title,
            reference=obj.reference,
            initiative_type=obj.initiative_type,
            initiative_type_alt=obj.initiative_type_alt,
            place=obj.place,
            created=obj.created,
            updated=obj.updated,
            history=list(obj.history or []),
            status=obj.status,
            url=obj.url,
            extra=obj.extra,
            authors=_authors(obj),
            deputies=list(obj.author_deputies or []),
            tagged=_tagged(obj, kb),
        )


class InitiativeExtendedSchema(BaseSchema):
    id: str
    title: str | None = None
    reference: str | None = None
    initiative_type: str | None = None
    initiative_type_alt: str | None = None
    place: str | None = None
    created: datetime | None = None
    updated: datetime | None = None
    history: list[str] = []
    status: str | None = None
    url: str | None = None
    content: str | None = None
    extra: dict | None = None
    authors: list[str] = []
    deputies: list[str] = []
    tagged: list[TaggedOut] = []

    @classmethod
    def from_doc(cls, obj, kb):
        return cls(
            id=obj.id,
            title=obj.title,
            reference=obj.reference,
            initiative_type=obj.initiative_type,
            initiative_type_alt=obj.initiative_type_alt,
            place=obj.place,
            created=obj.created,
            updated=obj.updated,
            history=list(obj.history or []),
            status=obj.status,
            url=obj.url,
            content="\n".join(obj.content or []),
            extra=obj.extra,
            authors=_authors(obj),
            deputies=list(obj.author_deputies or []),
            tagged=_tagged(obj, kb),
        )
