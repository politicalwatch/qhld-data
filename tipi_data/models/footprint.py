from datetime import datetime

from pydantic import Field

from tipi_data.models.base import DocBase, MongoModel


class FootprintElement(DocBase):
    name: str | None = None
    score: float | None = None

    def __str__(self):
        return f"{self.name}: {self.score}"


class FootprintByTopic(MongoModel):
    name: str | None = None
    deputies: list[FootprintElement] = Field(default_factory=list)
    parliamentarygroups: list[FootprintElement] = Field(default_factory=list)
    computed_at: datetime = Field(default_factory=datetime.now)


class FootprintByDeputy(MongoModel):
    name: str | None = None
    score: float | None = None
    topics: list[FootprintElement] = Field(default_factory=list)
    computed_at: datetime = Field(default_factory=datetime.now)


class FootprintByParliamentaryGroup(MongoModel):
    name: str | None = None
    score: float | None = None
    topics: list[FootprintElement] = Field(default_factory=list)
    computed_at: datetime = Field(default_factory=datetime.now)
