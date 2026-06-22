from pydantic import Field

from tipi_data.models.base import DocBase, MongoModel


class Tag(DocBase):
    tag: str | None = None
    subtopic: str | None = None
    regex: str | None = None
    shuffle: bool | None = None

    def __str__(self):
        return self.tag


class Topic(MongoModel):
    name: str | None = None
    shortname: str | None = None
    description: list[str] = Field(default_factory=list)
    tags: list[Tag] = Field(default_factory=list)
    knowledgebase: str | None = None
    public: bool | None = None

    def __str__(self):
        return self.name
