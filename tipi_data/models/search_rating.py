"""One user's rating of one speech search.

Append-only: every submission is its own document, so a rater changing their mind
is preserved as signal instead of overwriting the earlier answer. Deduplicating is
left to whoever reads the collection.

Unlike most documents here this one is ``extra="forbid"``. The payload originates
from a public endpoint, and a collection we intend to mine for search-quality and
NER gaps should not silently absorb whatever happened to be posted at it.
"""

from datetime import datetime, timezone

from bson import ObjectId
from pydantic import ConfigDict, Field

from tipi_data.models.base import DocBase


class SearchRating(DocBase):
    model_config = ConfigDict(extra="forbid")

    # Optional so a fresh rating dumps without an ``_id`` and Mongo assigns one.
    id: ObjectId | None = Field(default=None, alias="_id")

    rating: int
    query: str
    # What the parser understood: semantic_query, filters, browse and — the reason
    # this is worth storing at all — ``unresolved``, the people it failed to
    # recognise. A low rating next to a non-empty ``unresolved`` is a NER candidate.
    query_meta: dict = Field(default_factory=dict)
    # Only offered for a low rating, so an empty list on a 4-5 means "not asked",
    # not "nothing was wrong".
    reasons: list[str] = Field(default_factory=list)
    comment: str | None = None
    result_ids: list[str] = Field(default_factory=list)
    results_count: int = 0
    # Which extraction run was being judged, so a rating is never read against a
    # corpus that has since been replaced.
    corpus: str | None = None
    # Aware UTC, as in DatasetUpdates: the client is not ``tz_aware``, so this reads
    # back naive UTC and the caller rendering it is the one to say so.
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))

    def __str__(self):
        return f"{self.rating}/5 {self.query}"
