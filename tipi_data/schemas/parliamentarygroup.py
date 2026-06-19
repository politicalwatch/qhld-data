from tipi_data.models.footprint import FootprintByParliamentaryGroup
from tipi_data.schemas.base import BaseSchema, FootprintElementOut


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
    def from_doc(cls, obj):
        try:
            fbg = FootprintByParliamentaryGroup.objects.get(id=obj.id)
            score = fbg.score
            topics = [FootprintElementOut.model_validate(t) for t in fbg.topics]
        except Exception:
            score = 0.0
            topics = []
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


class ParliamentaryGroupCompactSchema(BaseSchema):
    # All model fields, no footprint (no per-row query).
    id: str
    name: str | None = None
    shortname: str | None = None
    composition: CompositionOut | None = None
    parties: list[str] = []
    color: str | None = None
