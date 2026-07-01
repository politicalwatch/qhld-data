from tipi_data import DoesNotExist, db
from tipi_data.models.speech import Speech


class Speeches:
    @staticmethod
    def save(speech: Speech):
        return db.speeches.replace_one(
            {"_id": speech.id}, speech.to_bson(), upsert=True)

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
    def by_references(references):
        """Yield the speeches of the given initiative references."""
        for doc in db.speeches.find({"reference": {"$in": list(references)}}):
            yield Speech.model_validate(doc)
