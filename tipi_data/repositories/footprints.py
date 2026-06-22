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
