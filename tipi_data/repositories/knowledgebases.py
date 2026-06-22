from tipi_data import db


class KnowledgeBases():
    @staticmethod
    def get_all():
        return db.topics.distinct('knowledgebase')

    @staticmethod
    def get_public():
        return db.topics.distinct('knowledgebase', {'public': True})
