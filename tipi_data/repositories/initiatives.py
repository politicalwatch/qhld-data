from tipi_data import DoesNotExist, db
from tipi_data.models.initiative import Initiative


def _kb_query(kb):
    """Initiatives tagged for a knowledge base (with at least one topic).
    Shared by ``by_kb``/``count_by_kb``/``aggregate_by_kb`` so the filter stays
    in one place."""
    return {
        "tagged": {"$elemMatch": {"knowledgebase": kb, "topics": {"$not": {"$size": 0}}}}
    }


# Projection used by the reference/status finders that previously did
# ``.only('reference', 'status')`` (the extractor also reads initiative_type_alt).
_REFS_PROJECTION = {"reference": 1, "status": 1, "initiative_type_alt": 1}


class Initiatives:
    @staticmethod
    def get(id):
        doc = db.initiatives.find_one({"_id": id})
        if doc is None:
            raise DoesNotExist(f"Initiative {id} does not exist")
        return Initiative.model_validate(doc)

    @staticmethod
    def save(initiative):
        return db.initiatives.replace_one(
            {"_id": initiative.id}, initiative.to_bson(), upsert=True)

    @staticmethod
    def get_one_non_answer_by_reference(reference):
        doc = db.initiatives.find_one(
            {"reference": reference, "initiative_type_alt": {"$ne": "Respuesta"}})
        if doc is None:
            raise DoesNotExist(
                f"Initiative {reference} (non-answer) does not exist")
        return Initiative.model_validate(doc)

    @staticmethod
    def get_answer_by_reference(reference):
        doc = db.initiatives.find_one(
            {"reference": reference, "initiative_type_alt": "Respuesta"})
        if doc is None:
            raise DoesNotExist(
                f"Initiative {reference} (answer) does not exist")
        return Initiative.model_validate(doc)

    @staticmethod
    def get_first_by_reference(reference):
        doc = db.initiatives.find_one(
            {"reference": reference}, sort=[("updated", -1)])
        return Initiative.model_validate(doc) if doc is not None else None

    @staticmethod
    def get_by_type_refs(type_code):
        return [
            Initiative.model_validate(d)
            for d in db.initiatives.find(
                {"initiative_type": type_code}, _REFS_PROJECTION).sort("reference", 1)
        ]

    @staticmethod
    def get_non_answers_refs():
        return [
            Initiative.model_validate(d)
            for d in db.initiatives.find(
                {"initiative_type_alt": {"$ne": "Respuesta"}}, _REFS_PROJECTION
            ).sort("reference", 1)
        ]

    @staticmethod
    def count_by_kb(kb):
        return db.initiatives.count_documents(_kb_query(kb))

    @staticmethod
    def aggregate(pipeline):
        return list(db.initiatives.aggregate(pipeline))

    @staticmethod
    def aggregate_by_kb(kb, pipeline):
        return list(db.initiatives.aggregate([{"$match": _kb_query(kb)}] + pipeline))

    @staticmethod
    def unset_tagged_all():
        return db.initiatives.update_many({}, {"$unset": {"tagged": 1}})

    @staticmethod
    def pull_tagged_by_kb(kb):
        return db.initiatives.update_many(
            {}, {"$pull": {"tagged": {"knowledgebase": kb}}})

    @staticmethod
    def unset_tagged_by_reference(reference):
        return db.initiatives.update_many(
            {"reference": reference}, {"$unset": {"tagged": 1}})

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
        return Initiatives.by_query(_kb_query(kb))

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
