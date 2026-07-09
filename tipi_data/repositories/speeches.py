from tipi_data import DoesNotExist, db
from tipi_data.models.speech import Speech


class Speeches:
    @staticmethod
    def save(speech: Speech):
        """Upsert a speech, accumulating its ``references`` roster.

        Speeches are extracted per initiative ``reference``, so an accumulated
        debate writes the same intervention once per initiative it addresses. A
        plain ``replace_one`` would reset the roster to the single reference of
        the current run; instead we ``$set`` the (stable) speech data and
        ``$addToSet`` the references, so the roster grows as more of the debate's
        initiatives are extracted. Same pattern as ``Sessions.save``."""
        doc = speech.to_bson()
        references = doc.pop("references", [])
        doc.pop("_id", None)
        update = {"$set": doc}
        if references:
            update["$addToSet"] = {"references": {"$each": references}}
        return db.speeches.update_one({"_id": speech.id}, update, upsert=True)

    @staticmethod
    def get(id):
        doc = db.speeches.find_one({"_id": id})
        if doc is None:
            raise DoesNotExist(f"Speech {id} does not exist")
        return Speech.model_validate(doc)

    @staticmethod
    def all():
        """Yield every stored speech (cursor-backed, for indexing the whole corpus)."""
        for doc in db.speeches.find():
            yield Speech.model_validate(doc)

    @staticmethod
    def count_by_reference(reference):
        """Number of stored speeches belonging to the given initiative reference."""
        return db.speeches.count_documents({"references": reference})

    @staticmethod
    def delete(id):
        """Remove a stored speech."""
        return db.speeches.delete_one({"_id": id})

    @staticmethod
    def by_references(references):
        """Yield the speeches of the given initiative references."""
        for doc in db.speeches.find({"references": {"$in": list(references)}}):
            yield Speech.model_validate(doc)

    @staticmethod
    def count_by_query(query):
        return db.speeches.count_documents(query)

    @staticmethod
    def by_query_paginated(query, limit=None, skip=None):
        """Speeches matching ``query``, optionally paginated.

        Sorted by ``order`` ascending when the query is scoped to a single sitting
        (``session_id``), so a session reads in the natural order interventions were
        delivered; otherwise most recent first (``date`` desc, then ``order``)."""
        if "session_id" in query:
            sort = [("order", 1)]
        else:
            sort = [("date", -1), ("order", 1)]
        cursor = db.speeches.find(query).sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return [Speech.model_validate(d) for d in cursor]

    @staticmethod
    def distinct_nondeputy_speakers():
        """Distinct ``{speaker, role}`` of everyone who has spoken but sits in no
        parliamentary group (``group`` null/empty) and is not labelled a plain
        deputy — government members and comparecencia witnesses. Seeds a catalog of
        non-deputy people who speak in Congress, so they can be recognised when
        *mentioned* in other speeches. Grows automatically as more sessions import."""
        pipeline = [
            {"$match": {
                "group": {"$in": [None, ""]},
                "speaker": {"$nin": [None, ""]},
                "role": {"$not": {"$regex": "Diputad", "$options": "i"}},
            }},
            {"$group": {"_id": {"speaker": "$speaker", "role": "$role"}}},
        ]
        return [
            {"speaker": doc["_id"]["speaker"], "role": doc["_id"].get("role")}
            for doc in db.speeches.aggregate(pipeline)
        ]
