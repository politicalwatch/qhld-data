from tipi_data.models.base import MongoModel


class InitiativeType(MongoModel):
    name: str | None = None
    group: str | None = None

    def __str__(self):
        return "{} : {}/{}".format(self.group, self.id, self.name)
