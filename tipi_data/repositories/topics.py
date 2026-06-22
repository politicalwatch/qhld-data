from tipi_data import DoesNotExist, db
from tipi_data.models.topic import Topic

# Natural, case-insensitive ordering performed in MongoDB (replaces natsort):
# numericOrdering -> "Tema 2" before "Tema 10"; strength 2 -> case-insensitive.
# Verified to match the previous natsort(ns.IGNORECASE) output on the real topics.
_NATURAL = {"locale": "es", "numericOrdering": True, "strength": 2}


def _kb_query(kb):
    if not isinstance(kb, list):
        kb = [kb]
    return {"knowledgebase": {"$in": kb}}


class Topics():
    @staticmethod
    def get_all():
        return [Topic.model_validate(d) for d in db.topics.find().sort("name", 1)]

    @staticmethod
    def get_all_sorted():
        return [Topic.model_validate(d)
                for d in db.topics.find().sort("name", 1).collation(_NATURAL)]

    @staticmethod
    def get_public():
        return [Topic.model_validate(d) for d in
                db.topics.find({"public": True}).sort("name", 1).collation(_NATURAL)]

    @staticmethod
    def get(id):
        doc = db.topics.find_one({"_id": id})
        if doc is None:
            raise DoesNotExist(f"Topic {id} does not exist")
        return Topic.model_validate(doc)

    @staticmethod
    def by_kb(kb):
        return [Topic.model_validate(d) for d in db.topics.find(_kb_query(kb))]

    @staticmethod
    def by_kb_sorted(kb):
        return [Topic.model_validate(d) for d in
                db.topics.find(_kb_query(kb)).sort("name", 1).collation(_NATURAL)]

    @staticmethod
    def get_subtopics():
        return db.topics.distinct('tags.subtopic')

    @staticmethod
    def get_subtopics_by_kb(kb):
        return db.topics.distinct('tags.subtopic', _kb_query(kb))
