from tipi_data import DoesNotExist, db
from tipi_data.models.initiative_type import InitiativeType


class InitiativeTypes:
    @staticmethod
    def get_all():
        return [InitiativeType.model_validate(d)
                for d in db.initiative_types.find().sort("name", 1)]

    @staticmethod
    def get_by_name(name):
        doc = db.initiative_types.find_one({"name": name})
        if doc is None:
            raise DoesNotExist(f"InitiativeType {name} does not exist")
        return InitiativeType.model_validate(doc)

    @staticmethod
    def get_names_by_group(group):
        return [d["name"]
                for d in db.initiative_types.find({"group": group}, {"name": 1})]
