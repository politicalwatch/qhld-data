from tipi_data import DoesNotExist, db
from tipi_data.models.stats import Stats as StatsModel


class Stats:
    @staticmethod
    def get():
        doc = db.statistics.find_one({})
        if doc is None:
            raise DoesNotExist("Stats do not exist")
        return StatsModel.model_validate(doc)

    @staticmethod
    def delete_all():
        return db.statistics.delete_many({})

    @staticmethod
    def save(stats):
        # Stats is a singleton with no stable _id; callers wipe then insert a
        # fresh document (mirrors the old ``Stats.objects().delete(); save()``).
        return db.statistics.insert_one(stats.to_bson())
