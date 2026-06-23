from tipi_data import db
from tipi_data.models.video import Video


class Videos:
    @staticmethod
    def save(video: Video):
        return db.videos.replace_one(
            {"_id": video.id}, video.to_bson(), upsert=True)
