from pymongo.errors import DuplicateKeyError

from tipi_data import db
from tipi_data.models.query_gap import QueryGap, QueryGapEvent


# How many verbatim sightings a document keeps. Pushed with a NEGATIVE $slice, so these
# are the most RECENT ones: the question a reviewer asks is how a gap behaves now, after
# whatever we changed, and the first five sightings answer a question about the past.
EXAMPLES_KEPT = 5


class QueryGaps:
    @staticmethod
    def record(event: QueryGapEvent):
        """Fold one sighting into its ``(field, key, outcome)`` document.

        An upsert with counters rather than an append-only insert: a popular gap must not
        cost more storage than a rare one, and the counts are the artifact a curation
        round actually reads. The document therefore stays a fixed size — the arrays are
        sets or capped — no matter how many times the gap is seen.
        """
        month = event.at.strftime("%Y-%m")
        add_to_set = {
            "surface_forms": event.value,
            # Kept even when null: "we saw this and had no candidate to suggest" is a
            # different finding from "we suggested X", and it is the one that means a
            # person is missing from the catalog entirely.
            "suggestions": event.suggestion,
        }
        if event.chosen is not None:
            add_to_set["chosen"] = event.chosen
        if event.tied:
            add_to_set["tied"] = {"$each": event.tied}
        update = {
            "$setOnInsert": {"first_seen": event.at},
            "$set": {"last_seen": event.at},
            "$inc": {
                "count": 1,
                "blocking_count": 1 if event.blocking else 0,
                f"counts_by_month.{month}": 1,
            },
            "$addToSet": add_to_set,
            "$push": {
                "examples": {
                    "$each": [{
                        "query": event.query,
                        "semantic_query": event.semantic_query,
                        "filters": event.filters,
                        "value": event.value,
                        "suggestion": event.suggestion,
                        "parser_model": event.parser_model,
                        "at": event.at,
                    }],
                    "$slice": -EXAMPLES_KEPT,
                }
            },
        }
        key = {"field": event.field, "key": event.key, "outcome": event.outcome}
        try:
            return db.query_gaps.update_one(key, update, upsert=True)
        except DuplicateKeyError:
            # Two searches raced to create the same brand-new gap and the unique index
            # rejected the loser. The document now exists, so the same update applies
            # cleanly; retried once so a race costs nothing rather than silently dropping
            # an observation from the counts.
            return db.query_gaps.update_one(key, update, upsert=True)

    @staticmethod
    def get_all():
        """Every gap, worst first: the ones that returned nothing to the most people."""
        return [QueryGap.model_validate(doc) for doc in
                db.query_gaps.find().sort([("blocking_count", -1), ("count", -1)])]

    @staticmethod
    def by_field(field):
        return [QueryGap.model_validate(doc) for doc in
                db.query_gaps.find({"field": field}).sort("count", -1)]
