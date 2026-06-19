from tipi_data.models.initiative import Initiative


class Initiatives:
    @staticmethod
    def get(id):
        return Initiative.objects().get(id=id)

    @staticmethod
    def get_all():
        return Initiative.objects()

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
        result = Initiatives.by_query(query).fields("created").order_by("-created")
        if not result:
            return None
        return result.first()["created"]

    @staticmethod
    def sitemap():
        """Lightweight projection (id + updated only) for building the frontend
        initiatives sitemap without loading full documents."""
        return Initiative.objects().only("id", "updated")

    @staticmethod
    def by_query(query):
        if "$text" in query.keys():
            return Initiative.objects(__raw__=query).order_by()

        return Initiative.objects(__raw__=query)

    @staticmethod
    def by_reference(reference):
        return Initiative.objects(reference=reference)
