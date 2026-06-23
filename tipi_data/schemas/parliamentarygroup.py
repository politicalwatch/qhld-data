from tipi_data.repositories.footprints import Footprints
from tipi_data.schemas.base import BaseSchema, FootprintElementOut


def _score_topics(fbg):
    """Turn a ``FootprintByParliamentaryGroup`` (or ``None``) into
    ``(score, topics)``. A missing footprint serializes as ``0.0`` / ``[]``."""
    if fbg is None:
        return 0.0, []
    topics = [FootprintElementOut.model_validate(t) for t in fbg.topics]
    return fbg.score, topics


class GenderOut(BaseSchema):
    female: int | None = None
    male: int | None = None


class AgesOut(BaseSchema):
    under35: int | None = None
    between35and49: int | None = None
    between50and65: int | None = None
    over65: int | None = None


class CompositionOut(BaseSchema):
    deputies: int | None = None
    gender: GenderOut | None = None
    ages: AgesOut | None = None


class ParliamentaryGroupSchema(BaseSchema):
    id: str
    name: str | None = None
    shortname: str | None = None
    composition: CompositionOut | None = None
    parties: list[str] = []
    color: str | None = None
    footprint: float | None = None
    footprint_by_topics: list[FootprintElementOut] = []

    @classmethod
    def from_doc(cls, obj, footprint=None):
        score, topics = (
            footprint
            if footprint is not None
            else _score_topics(Footprints.get_by_parliamentarygroup_id(obj.id))
        )
        return cls(
            id=obj.id,
            name=obj.name,
            shortname=obj.shortname,
            composition=obj.composition,
            parties=list(obj.parties or []),
            color=obj.color,
            footprint=score,
            footprint_by_topics=topics,
        )

    @classmethod
    def from_docs(cls, objs):
        """Serialize a list of groups with a single footprint query (no N+1)."""
        objs = list(objs)
        footprints = Footprints.get_by_parliamentarygroup_ids(o.id for o in objs)
        return [
            cls.from_doc(o, footprint=_score_topics(footprints.get(o.id)))
            for o in objs
        ]


class ParliamentaryGroupCompactSchema(BaseSchema):
    # All model fields, no footprint (no per-row query).
    id: str
    name: str | None = None
    shortname: str | None = None
    composition: CompositionOut | None = None
    parties: list[str] = []
    color: str | None = None
