from tipi_data import DoesNotExist, db
from tipi_data.models.initiative import Initiative


class Initiatives:
    @staticmethod
    def get(id):
        doc = db.initiatives.find_one({"_id": id})
        if doc is None:
            raise DoesNotExist(f"Initiative {id} does not exist")
        return Initiative.model_validate(doc)

    @staticmethod
    def get_all():
        return [Initiative.model_validate(d)
                for d in db.initiatives.find().sort("updated", -1)]

    @staticmethod
    def get_all_short_untagged():
        query = {
            "$and": [
                {
                    "$or": [
                        {"tagged": []},
                        {"tagged": {"$exists": False}},
                    ]
                },
                {"content.100000": {"$exists": False}},
            ]
        }
        return Initiatives.by_query(query)

    @staticmethod
    def get_all_long_untagged():
        query = {
            "$and": [
                {
                    "$or": [
                        {"tagged": []},
                        {"tagged": {"$exists": False}},
                    ]
                },
                {"content.100000": {"$exists": True}},
            ]
        }
        return Initiatives.by_query(query)

    @staticmethod
    def get_all_without_answers():
        query = {"initiative_type_alt": {"$ne": "Respuesta"}}
        return Initiatives.by_query(query)

    @staticmethod
    def by_kb(kb):
        query = {
            "tagged": {
                "$elemMatch": {"knowledgebase": kb, "topics": {"$not": {"$size": 0}}}
            }
        }
        return Initiatives.by_query(query)

    @staticmethod
    def by_kb_untagged(kb):
        query = {
            "tagged.knowledgebase": {"$ne": kb},
        }
        return Initiatives.by_query(query)

    @staticmethod
    def by_kb_short_untagged(kb):
        query = {
            "$and": [
                {"tagged.knowledgebase": {"$ne": kb}},
                {"content.100000": {"$exists": False}},
            ]
        }
        return Initiatives.by_query(query)

    @staticmethod
    def by_kb_long_untagged(kb):
        query = {
            "$and": [
                {"tagged.knowledgebase": {"$ne": kb}},
                {"content.100000": {"$exists": True}},
            ]
        }
        return Initiatives.by_query(query)

    @staticmethod
    def by_tag(topic, tag):
        query = {"tagged.tags": {"$elemMatch": {"topic": topic, "tag": tag}}}
        return Initiatives.by_query(query)

    @staticmethod
    def get_all_untagged():
        query = {
            "$or": [
                {"tagged": []},
                {"tagged": {"$exists": False}},
            ]
        }
        return Initiatives.by_query(query)

    @staticmethod
    def get_last_valid_creation_date(entity=None, topic=None, typeof="deputy"):
        query = {
            "status": {"$not": {"$in": ["No admitida a trámite", "Retirada"]}},
        }
        if topic:
            query["tagged.topics"] = topic
        if entity:
            if typeof == "deputy":
                query["author_deputies"] = entity
            if typeof == "parliamentarygroup":
                query["author_parliamentarygroups"] = entity
        doc = db.initiatives.find_one(
            query, {"created": 1}, sort=[("created", -1)]
        )
        if not doc:
            return None
        return doc["created"]

    @staticmethod
    def sitemap():
        """Lightweight projection (id + updated only) for building the frontend
        initiatives sitemap without loading full documents."""
        return [
            Initiative.model_validate(d)
            for d in db.initiatives.find({}, {"_id": 1, "updated": 1}).sort("updated", -1)
        ]

    @staticmethod
    def by_query(query):
        cursor = db.initiatives.find(query)
        if "$text" not in query:
            cursor = cursor.sort("updated", -1)
        return [Initiative.model_validate(d) for d in cursor]

    @staticmethod
    def count_by_query(query):
        return db.initiatives.count_documents(query)

    @staticmethod
    def by_query_paginated(query, limit=None, skip=None):
        cursor = db.initiatives.find(query)
        if "$text" not in query:
            cursor = cursor.sort("updated", -1)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return [Initiative.model_validate(d) for d in cursor]

    @staticmethod
    def by_reference(reference):
        return [
            Initiative.model_validate(d)
            for d in db.initiatives.find({"reference": reference}).sort("updated", -1)
        ]
