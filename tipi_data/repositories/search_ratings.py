from tipi_data import db
from tipi_data.models.search_rating import SearchRating


class SearchRatings:
    @staticmethod
    def save(rating: SearchRating):
        """Store one rating.

        ``insert_one``, not the ``replace_one(..., upsert=True)`` the keyed models
        use: ratings are append-only, so rating the same search twice keeps both
        answers.
        """
        return db.search_ratings.insert_one(rating.to_bson())
