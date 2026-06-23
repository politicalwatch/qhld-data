from tipi_data import DoesNotExist, db
from tipi_data.models.footprint import (
    FootprintByTopic,
    FootprintByDeputy,
    FootprintByParliamentaryGroup,
)


class Footprints:
    @staticmethod
    def get_all_topics():
        return [FootprintByTopic.model_validate(d)
                for d in db.footprint_by_topics.find()]

    @staticmethod
    def save_topic(fp):
        return db.footprint_by_topics.replace_one(
            {"_id": fp.id}, fp.to_bson(), upsert=True)

    @staticmethod
    def save_deputy(fp):
        return db.footprint_by_deputies.replace_one(
            {"_id": fp.id}, fp.to_bson(), upsert=True)

    @staticmethod
    def save_parliamentarygroup(fp):
        return db.footprint_by_parliamentarygroups.replace_one(
            {"_id": fp.id}, fp.to_bson(), upsert=True)

    @staticmethod
    def aggregate_deputies(pipeline):
        return list(db.footprint_by_deputies.aggregate(pipeline))

    @staticmethod
    def get_by_topic(topic):
        doc = db.footprint_by_topics.find_one({"name": topic})
        if doc is None:
            raise DoesNotExist(f"FootprintByTopic {topic} does not exist")
        return FootprintByTopic.model_validate(doc)

    @staticmethod
    def get_range_by_all_topics():
        pipeline = [
            {
                "$project": {
                    "_id": 0,
                    "name": "$name",
                    "deputy": {
                        "max": {
                            "$first": {
                                "$filter": {
                                    "input": {
                                        "$sortArray": {
                                            "input": "$deputies",
                                            "sortBy": {"score": -1},
                                        }
                                    },
                                    "as": "deputy",
                                    "cond": {
                                        "$eq": [
                                            "$$deputy.score",
                                            {"$max": "$deputies.score"},
                                        ]
                                    },
                                }
                            }
                        },
                        "min": {
                            "$first": {
                                "$filter": {
                                    "input": {
                                        "$sortArray": {
                                            "input": "$deputies",
                                            "sortBy": {"score": 1},
                                        }
                                    },
                                    "as": "deputy",
                                    "cond": {"$gt": ["$$deputy.score", 0]},
                                }
                            }
                        },
                    },
                    "parliamentarygroup": {
                        "max": {
                            "$first": {
                                "$filter": {
                                    "input": {
                                        "$sortArray": {
                                            "input": "$parliamentarygroups",
                                            "sortBy": {"score": -1},
                                        }
                                    },
                                    "as": "pg",
                                    "cond": {
                                        "$eq": [
                                            "$$pg.score",
                                            {"$max": "$parliamentarygroups.score"},
                                        ]
                                    },
                                }
                            }
                        },
                        "min": {
                            "$first": {
                                "$filter": {
                                    "input": {
                                        "$sortArray": {
                                            "input": "$parliamentarygroups",
                                            "sortBy": {"score": 1},
                                        }
                                    },
                                    "as": "pg",
                                    "cond": {"$gt": ["$$pg.score", 0]},
                                }
                            }
                        },
                    },
                }
            },
            {"$sort": {"topic": 1}},
        ]
        return list(db.footprint_by_topics.aggregate(pipeline))

    @staticmethod
    def get_all_deputies():
        return [FootprintByDeputy.model_validate(d)
                for d in db.footprint_by_deputies.find()]

    @staticmethod
    def get_by_deputy(deputy):
        doc = db.footprint_by_deputies.find_one({"name": deputy})
        if doc is None:
            raise DoesNotExist(f"FootprintByDeputy {deputy} does not exist")
        return FootprintByDeputy.model_validate(doc)

    @staticmethod
    def get_by_deputy_id(id):
        """Footprint for a single deputy, keyed by ``_id`` (== the deputy id).
        Returns ``None`` when it hasn't been computed yet so serialization can
        degrade gracefully."""
        doc = db.footprint_by_deputies.find_one({"_id": id})
        return FootprintByDeputy.model_validate(doc) if doc is not None else None

    @staticmethod
    def get_by_deputy_ids(ids):
        """Footprints for many deputies in a single query, keyed by deputy id.
        Used to avoid an N+1 when serializing deputy lists."""
        return {
            fp.id: fp
            for fp in (
                FootprintByDeputy.model_validate(d)
                for d in db.footprint_by_deputies.find({"_id": {"$in": list(ids)}})
            )
        }

    @staticmethod
    def get_all_parliamentarygroups():
        return [FootprintByParliamentaryGroup.model_validate(d)
                for d in db.footprint_by_parliamentarygroups.find()]

    @staticmethod
    def get_by_parliamentarygroup(parliamentarygroup):
        doc = db.footprint_by_parliamentarygroups.find_one({"name": parliamentarygroup})
        if doc is None:
            raise DoesNotExist(
                f"FootprintByParliamentaryGroup {parliamentarygroup} does not exist")
        return FootprintByParliamentaryGroup.model_validate(doc)

    @staticmethod
    def get_by_parliamentarygroup_id(id):
        """Footprint for a single parliamentary group, keyed by ``_id`` (== the
        group id). Returns ``None`` when not yet computed."""
        doc = db.footprint_by_parliamentarygroups.find_one({"_id": id})
        return (
            FootprintByParliamentaryGroup.model_validate(doc)
            if doc is not None
            else None
        )

    @staticmethod
    def get_by_parliamentarygroup_ids(ids):
        """Footprints for many parliamentary groups in a single query, keyed by
        group id. Used to avoid an N+1 when serializing group lists."""
        return {
            fp.id: fp
            for fp in (
                FootprintByParliamentaryGroup.model_validate(d)
                for d in db.footprint_by_parliamentarygroups.find(
                    {"_id": {"$in": list(ids)}}
                )
            )
        }
