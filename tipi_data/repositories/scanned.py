import re

from tipi_data import DoesNotExist, db
from tipi_data.models.scanned import Scanned as ScannedModel


class Scanned():
    @staticmethod
    def get(id):
        doc = db.scanned.find_one({"_id": id})
        if doc is None:
            raise DoesNotExist(f"Scanned {id} does not exist")
        return ScannedModel.model_validate(doc)

    @staticmethod
    def save(scanned: ScannedModel):
        return db.scanned.replace_one(
            {"_id": scanned.id}, scanned.to_bson(), upsert=True)

    @staticmethod
    def search_verified(query):
        return [ScannedModel.model_validate(d)
                for d in db.scanned.find(
                    {"title": re.compile(query, re.IGNORECASE), "verified": True})]

    @staticmethod
    def delete_expired(date):
        return db.scanned.delete_many({"expiration": {"$lte": date}})

    @staticmethod
    def get_unverified_since(date):
        return [ScannedModel.model_validate(d)
                for d in db.scanned.find(
                    {"created": {"$gte": date}, "verified": False})]
