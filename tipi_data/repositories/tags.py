from tipi_data import DoesNotExist, db
from tipi_data.models.topic import Topic

import itertools
import regex


def compile_tag(topic, tag):
    delimiter = ".*?" if ".*?" in tag["regex"] else ".*"
    if tag["shuffle"]:
        tags = []
        for permutation in itertools.permutations(tag["regex"].split(delimiter)):
            try:
                tags.append(
                    {
                        "topic": topic["name"],
                        "subtopic": tag["subtopic"],
                        "tag": tag["tag"],
                        "knowledgebase": topic["knowledgebase"],
                        "public": topic["public"],
                        "compiletag": regex.compile(
                            "(?i)" + delimiter.join(permutation)
                        ),
                    }
                )
            except regex.error as e:
                print(e, tag["regex"])
        return tags

    try:
        return [
            {
                "topic": topic["name"],
                "subtopic": tag["subtopic"],
                "tag": tag["tag"],
                "knowledgebase": topic["knowledgebase"],
                "public": topic["public"],
                "compiletag": regex.compile("(?i)" + tag["regex"]),
            }
        ]
    except regex.error as e:
        print(e, topic["name"], tag["subtopic"], tag["regex"])


class Tags:
    @staticmethod
    def get_all():
        tags = []
        for doc in db.topics.find():
            topic = Topic.model_validate(doc)
            for tag in topic["tags"]:
                compiled_tags = compile_tag(topic, tag)
                if compiled_tags:
                    tags = tags + compiled_tags
        return tags

    @staticmethod
    def by_name(topic, tag):
        doc = db.topics.find_one({"name": topic})
        if doc is None:
            raise DoesNotExist(f"Topic {topic} does not exist")
        topic = Topic.model_validate(doc)
        try:
            return compile_tag(
                topic, list(filter(lambda x: x["tag"] == tag, topic["tags"]))[0]
            )
        except KeyError:
            return None
        except IndexError:
            return None

    @staticmethod
    def by_topic(topic):
        tags = []
        doc = db.topics.find_one({"name": topic})
        if doc is None:
            raise DoesNotExist(f"Topic {topic} does not exist")
        topic = Topic.model_validate(doc)
        try:
            for tag in topic["tags"]:
                compiled_tags = compile_tag(topic, tag)
                if compiled_tags:
                    tags = tags + compiled_tags
            return tags
        except KeyError:
            return []
        except IndexError:
            return []

    @staticmethod
    def by_kb(kb):
        tags = []
        for doc in db.topics.find({"knowledgebase": kb}):
            topic = Topic.model_validate(doc)
            for tag in topic["tags"]:
                compiled_tags = compile_tag(topic, tag)
                if compiled_tags:
                    tags = tags + compiled_tags
        return tags
