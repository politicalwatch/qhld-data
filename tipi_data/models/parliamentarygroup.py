from pydantic import Field

from tipi_data.models.base import DocBase, MongoModel


class Gender(DocBase):
    female: int | None = None
    male: int | None = None


class Ages(DocBase):
    under35: int | None = None
    between35and49: int | None = None
    between50and65: int | None = None
    over65: int | None = None


class ParliamentaryGroupComposition(DocBase):
    deputies: int | None = None
    gender: Gender | None = None
    ages: Ages | None = None


class ParliamentaryGroup(MongoModel):
    name: str | None = None
    shortname: str | None = None
    composition: ParliamentaryGroupComposition | None = None
    parties: list[str] = Field(default_factory=list)
    color: str | None = None

    def __str__(self):
        return self.name
