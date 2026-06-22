from datetime import datetime

from tipi_data import DoesNotExist, db
from tipi_data.models.deputy import Deputy


def _actives(extra=None):
    """Filter for active deputies, optionally merged with extra criteria
    (replaces the mongoengine ``Deputy.actives`` queryset manager)."""
    query = {"active": True}
    if extra:
        query.update(extra)
    return query


class Deputies:
    @staticmethod
    def get_all():
        return [Deputy.model_validate(d)
                for d in db.deputies.find().sort("name", 1)]

    @staticmethod
    def get(id):
        doc = db.deputies.find_one({"_id": id})
        if doc is None:
            raise DoesNotExist(f"Deputy {id} does not exist")
        return Deputy.model_validate(doc)

    @staticmethod
    def get_by_query(query):
        return [Deputy.model_validate(d)
                for d in db.deputies.find(query).sort("name", 1)]

    @staticmethod
    def get_total(group):
        return db.deputies.count_documents(
            _actives({"parliamentarygroup": group})
        )

    @staticmethod
    def get_total_females(group):
        return db.deputies.count_documents(
            _actives({"parliamentarygroup": group, "gender": "Mujer"})
        )

    @staticmethod
    def get_total_males(group):
        return db.deputies.count_documents(
            _actives({"parliamentarygroup": group, "gender": "Hombre"})
        )

    @staticmethod
    def get_total_under_35(group):
        return db.deputies.count_documents(
            _actives({"parliamentarygroup": group, "age": {"$lt": 35}})
        )

    @staticmethod
    def get_total_between_35_and_49(group):
        return Deputies.get_total_between_ages(group, 35, 49)

    @staticmethod
    def get_total_between_50_and_65(group):
        return Deputies.get_total_between_ages(group, 50, 65)

    @staticmethod
    def get_total_between_ages(group, gt, lt):
        return db.deputies.count_documents(
            _actives({"parliamentarygroup": group, "age": {"$gte": gt, "$lte": lt}})
        )

    @staticmethod
    def get_total_over_65(group):
        return db.deputies.count_documents(
            _actives({"parliamentarygroup": group, "age": {"$gt": 65}})
        )

    @staticmethod
    def get_birthdays():
        pipeline = [
                {'$match': {'active': True}},
                {'$addFields': {
                    'id': '$_id',
                    'birthDay': {'$dayOfMonth': '$birthdate'},
                    'birthMonth': {'$month': '$birthdate'},
                    'todayDay': {'$dayOfMonth': datetime.today()},
                    'todayMonth': {'$month': datetime.today()}
                    }
                 },
                {'$match': {
                    '$expr': {
                        '$and': [
                            {'$eq': ['$birthDay', '$todayDay']},
                            {'$eq': ['$birthMonth', '$todayMonth']}
                            ]
                        }
                    }
                 },
                {'$unset': ['_id', 'birthDay', 'birthMonth', 'todayDay', 'todayMonth']}
                ]
        return [
                Deputy.model_validate(doc)
                for doc in db.deputies.aggregate(pipeline)
                ]
