from tipi_data import db
from tipi_data.models.scanned import Scanned as ScannedModel


class Scanned():
    @staticmethod
    def delete_expired(date):
        return db.scanned.delete_many({"expiration": {"$lte": date}})

    @staticmethod
    def get_unverified_since(date):
        return [ScannedModel.model_validate(d)
                for d in db.scanned.find(
                    {"created": {"$gte": date}, "verified": False})]
