from tipi_data import DoesNotExist, db
from tipi_data.models.parliamentarygroup import Gender, \
        Ages, \
        ParliamentaryGroupComposition, \
        ParliamentaryGroup
from tipi_data.repositories.deputies import Deputies


class ParliamentaryGroups:
    @staticmethod
    def get_all():
        return [ParliamentaryGroup.model_validate(d)
                for d in db.parliamentarygroups.find().sort("composition.deputies", -1)]

    @staticmethod
    def get(id):
        doc = db.parliamentarygroups.find_one({"_id": id})
        if doc is None:
            raise DoesNotExist(f"ParliamentaryGroup {id} does not exist")
        return ParliamentaryGroup.model_validate(doc)

    @staticmethod
    def get_by_name(name):
        doc = db.parliamentarygroups.find_one({"name": name})
        if doc is None:
            raise DoesNotExist(f"ParliamentaryGroup {name} does not exist")
        return ParliamentaryGroup.model_validate(doc)

    @staticmethod
    def get_by_query(query):
        return [ParliamentaryGroup.model_validate(d)
                for d in db.parliamentarygroups.find(query).sort("composition.deputies", -1)]

    @staticmethod
    def get_composition(short_group):
        return ParliamentaryGroupComposition(
                deputies=Deputies.get_total(short_group),
                gender=Gender(
                    female=Deputies.get_total_females(short_group),
                    male=Deputies.get_total_males(short_group)
                    ),
                ages=Ages(
                    under35=Deputies.get_total_under_35(short_group),
                    between35and49=Deputies.get_total_between_35_and_49(short_group),
                    between50and65=Deputies.get_total_between_50_and_65(short_group),
                    over65=Deputies.get_total_over_65(short_group)
                    )
                )
