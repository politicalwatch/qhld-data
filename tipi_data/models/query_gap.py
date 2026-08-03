"""What speech search could not identify, aggregated per surface form.

Every natural-language search reports the values its parser could not resolve — a person,
a theme, a constituency — and, since the resolver learned to say so, the values it *did*
resolve only by breaking a tie arbitrarily. Both are gaps in our catalogs, discoverable
with no user action at all, and they used to be logged and thrown away. This collection
keeps them so a curation round can work from evidence instead of guesses.

Two models, because an observation is not the stored document. ``QueryGapEvent`` is one
sighting, handed to the repository; the repository folds it into one document per
``(field, key, outcome)``, which is what ``QueryGap`` reads back. The counters and the
capped example list are what keep that document a fixed size no matter how popular the
gap is.

Not public, and not kept: the plan is to review this collection and delete it. The values
in it are names of people who appear in public parliamentary records, plus the queries
that named them.
"""

from datetime import datetime, timezone

from bson import ObjectId
from pydantic import ConfigDict, Field

from tipi_data.models.base import DocBase


# One sighting can only ever be one of these.
UNRESOLVED = "unresolved"   # matched nothing usable — a missing person or a missing alias
AMBIGUOUS = "ambiguous"     # matched, but several candidates tied and one was picked


class QueryGapEvent(DocBase):
    """One unidentified (or arbitrarily identified) value from one search.

    ``extra="forbid"`` even though this never comes from a request: it is assembled by
    hand at the call site, and a typo in a field name would otherwise be stored as a
    brand-new field and noticed by nobody.
    """

    model_config = ConfigDict(extra="forbid")

    # Which filter the value was meant to fill ("mentions", "speaker", "entities") and
    # the canonical form of the value, which is what groups sightings together. The
    # caller derives the key with the same normalisation the resolver itself uses, so a
    # key here means the same thing it means in the search path.
    field: str
    key: str
    outcome: str
    # The surface form exactly as the query carried it. Kept verbatim because deciding
    # that two surfaces mean the same person is a judgement call made at review time,
    # not something the writer can settle: "Rueda" and "Alfonso Rueda" normalise apart,
    # and no automatic rule can join them without also joining two different Ruedas.
    value: str
    # True when the miss made the query unsatisfiable, i.e. a real person got zero
    # results. This is the priority ordering for a curation round.
    blocking: bool = False
    # The resolver's own hint, and the most useful field here: absent means nobody in the
    # catalog is close (a genuinely unknown person), "'X' (87)" means X exists but the
    # spelling did not reach the threshold (an alias gap), and "ambiguous: 'X' / 'Y'"
    # means the resolver refused a tie.
    suggestion: str | None = None
    # ``AMBIGUOUS`` only: who won the tie, and everyone who was in it.
    chosen: str | None = None
    tied: list[str] = Field(default_factory=list)
    # Context for adjudication. The topic and filters say what the query was ABOUT, which
    # is often what tells you which of two same-named people was meant.
    query: str
    semantic_query: str | None = None
    filters: dict = Field(default_factory=dict)
    # Which parser produced this reading. An empty string is a legitimate value meaning
    # "no model was pinned, the provider default decided" — not missing data.
    parser_model: str | None = None
    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QueryGap(DocBase):
    """The aggregate the repository maintains — one per ``(field, key, outcome)``.

    Read side only; nothing writes this model. Two of its fields are worth knowing about
    when reviewing:

    ``suggestions`` accumulates every distinct hint ever seen, so it doubles as a record
    of our own changes: a row whose hints go from nothing to "'X' (87)" is a row where a
    catalog entry landed underneath it. And more than one value in ``chosen`` is proof
    that an ``AMBIGUOUS`` row is genuinely unstable — the tie is decided by the order of
    a set, so the same query can resolve to a different person after a restart.

    ``counts_by_month`` is what answers "is this still a gap": if the month after a fix
    never appears, the row is done.
    """

    id: ObjectId | None = Field(default=None, alias="_id")

    field: str
    key: str
    outcome: str
    surface_forms: list[str] = Field(default_factory=list)
    count: int = 0
    blocking_count: int = 0
    counts_by_month: dict = Field(default_factory=dict)
    suggestions: list[str | None] = Field(default_factory=list)
    chosen: list[str] = Field(default_factory=list)
    tied: list[str] = Field(default_factory=list)
    examples: list[dict] = Field(default_factory=list)
    first_seen: datetime | None = None
    last_seen: datetime | None = None

    def __str__(self):
        return f"{self.field}:{self.key} ×{self.count} ({self.outcome})"
