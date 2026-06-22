from tipi_data.models.base import MongoModel


class Place(MongoModel):
    name: str | None = None

    def __str__(self):
        return self.name
