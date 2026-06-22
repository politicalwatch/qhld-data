from datetime import datetime

from pydantic import Field

from tipi_data.models.base import MongoModel
from tipi_data.models.initiative import Tagged


class Scanned(MongoModel):
    title: str | None = None
    excerpt: str | None = None
    result: list[Tagged] = Field(default_factory=list)
    created: datetime | None = None
    expiration: datetime | None = None
    verified: bool | None = None

    def init_tagged_kb(self, kb):
        tagged = list(filter(lambda tagged: tagged.knowledgebase == kb, self.result))
        if len(tagged) > 0:
            return
        tagged = Tagged(knowledgebase=kb, topics=[], tags=[])
        self.result.append(tagged)

    def add_tag(self, kb, topic, subtopic, tag_name, times):
        tagged = list(filter(lambda tagged: tagged.knowledgebase == kb, self.result))

        if len(tagged) > 0:
            tagged = tagged[0]
        else:
            tagged = Tagged(knowledgebase=kb, topics=[], tags=[])
            self.result.append(tagged)

        tagged.add_tag(topic, subtopic, tag_name, times)
