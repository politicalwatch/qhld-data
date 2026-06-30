from tipi_data import db
from tipi_data.models.speech import Speech


class Speeches:
    @staticmethod
    def save(speech: Speech):
        return db.speeches.replace_one(
            {"_id": speech.id}, speech.to_bson(), upsert=True)
