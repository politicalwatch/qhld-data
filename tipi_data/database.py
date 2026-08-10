"""pymongo connection layer (replaces mongoengine).

Exposes a process-wide ``MongoClient`` and the ``db`` database handle used by the
repositories (e.g. ``db.initiatives.find_one(...)``), a ``DoesNotExist`` exception
(replacing ``mongoengine.queryset.DoesNotExist``), and ``ensure_indexes()``.

``MongoClient`` is created with pymongo defaults — no ``tz_aware`` / explicit
``uuidRepresentation`` — to preserve mongoengine's naive-datetime behaviour and
keep the on-disk BSON shape unchanged.
"""

from os import environ as env

from pymongo import ASCENDING, DESCENDING, MongoClient, TEXT
from pymongo.errors import PyMongoError

from . import config


client = MongoClient(
    host=config.MONGO_HOST,
    port=config.MONGO_PORT,
    username=config.MONGO_USER,
    password=config.MONGO_PASSWORD,
)
db = client[config.MONGO_DB]


class DoesNotExist(Exception):
    """Raised by repository ``get``-style lookups when no document matches.

    Replaces ``mongoengine.queryset.DoesNotExist`` as the public symbol consumers
    import via ``from tipi_data import DoesNotExist``.
    """


# Declared indexes, mirroring the mongoengine ``meta['indexes']`` definitions.
# ``(keys, options)`` pairs passed straight to ``create_index``.
_INDEXES = {
    "initiatives": [
        ([("title", TEXT), ("content", TEXT)], {"default_language": "spanish"}),
        ([("reference", ASCENDING)], {}),
        ([("updated", ASCENDING)], {}),
    ],
    "deputies": [([("name", ASCENDING)], {})],
    "topics": [([("name", ASCENDING)], {})],
    "places": [([("name", ASCENDING)], {})],
    "parliamentarygroups": [([("name", ASCENDING)], {})],
    "footprint_by_topics": [([("name", ASCENDING)], {})],
    "footprint_by_deputies": [([("name", ASCENDING)], {})],
    "footprint_by_parliamentarygroups": [([("name", ASCENDING)], {})],
    "speeches": [
        ([("references", ASCENDING)], {}),
        ([("session_id", ASCENDING)], {}),
        ([("date", ASCENDING)], {}),
        ([("video_id", ASCENDING)], {}),
    ],
    "sessions": [
        ([("date", ASCENDING)], {}),
        ([("references", ASCENDING)], {}),
    ],
    # Newest-first: every read of this collection is "what have users said lately".
    "search_ratings": [([("created_at", DESCENDING)], {})],
    # The unique one is the upsert key, not just an optimisation: it is what makes one
    # document per gap true even when two searches race to create the same one.
    "query_gaps": [
        ([("field", ASCENDING), ("key", ASCENDING), ("outcome", ASCENDING)],
         {"unique": True}),
        ([("last_seen", DESCENDING)], {}),
    ],
    # No entry for ``speech_alignments`` on purpose, and it survived the move to one
    # document per speech AND language. The key is composite ("<speech id>:<lang>") but
    # every read is still a lookup by ``_id``: a caller knows the candidate languages
    # from ``Speech.speech[].lang``, so even "which tracks does this speech have" is an
    # ``$in`` over two ids rather than a search on a field. The absence is a decision,
    # not an oversight.
}


def ensure_indexes():
    """Create the declared indexes. Idempotent — mirrors mongoengine's implicit
    index creation, so it is safe to call repeatedly and on already-provisioned
    databases."""
    for collection, specs in _INDEXES.items():
        for keys, options in specs:
            db[collection].create_index(keys, **options)


# Auto-create indexes on import (mongoengine did this lazily). Guarded so that
# importing the package offline — e.g. model-only unit tests with no MongoDB —
# never fails; set MONGO_SKIP_INDEX_INIT to skip entirely.
if not env.get("MONGO_SKIP_INDEX_INIT"):
    try:
        ensure_indexes()
    except PyMongoError:
        pass
