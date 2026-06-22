from datetime import datetime

from pydantic import Field

from tipi_data.models.base import DocBase, MongoModel


class Tag(DocBase):
    topic: str | None = None
    subtopic: str | None = None
    tag: str | None = None
    times: int | None = None

    def __str__(self):
        return self.tag

    def serialize(self):
        return {
            'topic': self.topic,
            'subtopic': self.subtopic,
            'tag': self.tag,
            'times': self.times
        }


class TopicAlignment(DocBase):
    topic: str | None = None
    percentage: float | None = None

    def __str__(self):
        return f"{self.topic}: {self.percentage}%"

    def serialize(self):
        return {
                'topic': self.topic,
                'percentage': self.percentage
                }


class Tagged(DocBase):
    knowledgebase: str | None = None
    topics: list[str] = Field(default_factory=list)
    topic_alignment: list[TopicAlignment] = Field(default_factory=list)
    tags: list[Tag] = Field(default_factory=list)

    def __str__(self):
        return self.knowledgebase

    def add_topic(self, topic):
        if topic not in self.topics:
            self.topics.append(topic)

    def add_tag(self, topic, subtopic, tag_name, times):
        if list(filter(lambda tag: tag.tag == tag_name and tag.subtopic == subtopic, self.tags)) == []:
            tag = Tag(topic=topic, subtopic=subtopic, tag=tag_name, times=times)
            self.tags.append(tag)
            self.add_topic(topic)

    def remove_single_occurences(self):
        topics_counter = dict()
        for tag in self.tags:
            if tag.topic in topics_counter.keys():
                topics_counter[tag.topic] += tag.times
            else:
                topics_counter[tag.topic] = tag.times
        for key in topics_counter.keys():
            if topics_counter[key] == 1:
                self.tags = list(filter(lambda x: x.topic != key, self.tags))
        self.topics = sorted(list(set([tag.topic for tag in self.tags])))

    def has_topics(self):
        return len(self.topics) > 0

    def serialize(self):
        return {
            'knowledgebase': self.knowledgebase,
            'topics': self.topics,
            'topic_alignment': list(map(lambda ta: ta.serialize(), self.topic_alignment)),
            'tags': list(map(lambda tag_set: tag_set.serialize(), self.tags))
        }


class Initiative(MongoModel):
    title: str | None = None
    reference: str | None = None
    initiative_type: str | None = None
    initiative_type_alt: str | None = None
    author_deputies: list[str] = Field(default_factory=list)
    author_parliamentarygroups: list[str] = Field(default_factory=list)
    author_others: list[str] = Field(default_factory=list)
    place: str | None = None
    created: datetime | None = None
    updated: datetime | None = None
    history: list[str] = Field(default_factory=list)
    status: str | None = None
    tagged: list[Tagged] = Field(default_factory=list)
    url: str | None = None
    content: list[str] = Field(default_factory=list)
    extra: dict = Field(default_factory=dict)

    def __str__(self):
        return "{} : {}".format(self.id, self.title)

    def untag(self):
        self.tagged = []

    def untag_kb(self, kb):
        tagged = list(filter(lambda tagged: tagged.knowledgebase != kb, self.tagged))
        self.tagged = tagged

    def init_tagged_kb(self, kb):
        tagged = list(filter(lambda tagged: tagged.knowledgebase == kb, self.tagged))
        if len(tagged) > 0:
            return
        tagged = Tagged(knowledgebase=kb, topics=[], tags=[])
        self.tagged.append(tagged)

    def add_tag(self, kb, topic, subtopic, tag_name, times):
        tagged = list(filter(lambda tagged: tagged.knowledgebase == kb, self.tagged))

        if len(tagged) > 0:
            tagged = tagged[0]
        else:
            tagged = Tagged(knowledgebase=kb, topics=[], tags=[])
            self.tagged.append(tagged)

        tagged.add_tag(topic, subtopic, tag_name, times)

    def remove_single_occurences(self):
        for tagged in self.tagged:
            tagged.remove_single_occurences()

    def has_tags(self):
        return any(tagged.has_topics for tagged in self.tagged)
