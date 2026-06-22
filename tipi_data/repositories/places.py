from tipi_data import db
from tipi_data.models.place import Place


class Places:
    @staticmethod
    def get_all():
        return [Place.model_validate(d) for d in db.places.find().sort("name", 1)]
