from tipi_data import DoesNotExist, db
from tipi_data.models.stats import Stats as StatsModel


class Stats:
    @staticmethod
    def get():
        doc = db.statistics.find_one({})
        if doc is None:
            raise DoesNotExist("Stats do not exist")
        return StatsModel.model_validate(doc)
