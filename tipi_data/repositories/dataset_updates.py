from datetime import datetime, timezone

from tipi_data import db


class DatasetUpdates:
    @staticmethod
    def touch(dataset: str):
        """Record ``dataset`` as refreshed right now.

        Stored as an aware UTC datetime; the ``MongoClient`` is deliberately not
        ``tz_aware``, so reads come back naive UTC and callers rendering the value
        are the ones to say so.
        """
        return db.dataset_updates.replace_one(
            {"_id": dataset},
            {"updated_at": datetime.now(timezone.utc)},
            upsert=True)

    @staticmethod
    def get_all() -> dict[str, datetime]:
        return {doc["_id"]: doc["updated_at"]
                for doc in db.dataset_updates.find()}
