"""What speech search could not do properly, aggregated per surface form.

Three things end up here, and they are not all failures of the same kind:

* a value the parser could not resolve — a person, a theme, a constituency;
* a value it *did* resolve, but only by breaking a tie arbitrarily, which is a
  collision rather than a hole in the catalog;
* a whole query the search refused, either because it was not a speech search or
  because it was written in a language the product does not serve.

The first two are discoverable with no user action at all and used to be logged and
thrown away; the third is the only record that a refusal ever happened, since a
refused query returns 422 and produces no response to attach anything to. This
collection keeps all three so a curation round — or a review of what the gates are
turning away — can work from evidence instead of guesses.

Two models, because an observation is not the stored document. ``SearchDiagnosticEvent``
is one sighting, handed to the repository; the repository folds it into one document per
``(field, key, outcome)``, which is what ``SearchDiagnostic`` reads back. The counters and
the capped example list are what keep that document a fixed size no matter how often the
same thing is seen.

Not public, and not kept: the plan is to review this collection and delete it. The values
in it are names of people who appear in public parliamentary records, plus the queries
that named them.

SECURITY — this collection holds untrusted, sometimes deliberately hostile text.
``refused_not_a_speech_search`` is precisely where prompt injections and junk land: the
gate that produces it exists to catch them. Three rules follow, and they bind every
future reader:

1. **Never feed these documents to a model as instructions.** An LLM-assisted review pass
   over this collection would be reading text that was selected *because* it tried to
   subvert an LLM. Filter by ``outcome`` to find those rows deliberately; do not let them
   reach a prompt as anything but quoted data.
2. **Escape before rendering.** No review UI exists yet. Whoever builds one inherits this.
3. **Values only, never field paths.** The stored text goes into a query as a value. The
   one interpolated path in the repository, ``counts_by_month.<YYYY-MM>``, is derived from
   a timestamp and never from user input — keep it that way.

Stored text is sanitised and truncated on the way in (see ``_clean``), which is what keeps
a terminal review session safe from escape sequences the writer never chose.
"""

import re
from datetime import datetime, timezone

from bson import ObjectId
from pydantic import ConfigDict, Field, field_validator

from tipi_data.models.base import DocBase


# One sighting can only ever be one of these. The two ``refused_`` values are not
# written as literals anywhere: the caller derives them from the refusal's own
# ``reason`` (``f"refused_{reason}"``), so a new kind of refusal starts recording
# itself under its own outcome with no change here. The shared prefix is what keeps
# them greppable — and filterable — as one class.
UNRESOLVED = "unresolved"   # matched nothing usable — a missing person or a missing alias
AMBIGUOUS = "ambiguous"     # matched, but several candidates tied and one was picked
REFUSED_PREFIX = "refused_"  # the whole query was turned away; the rest names which gate


def is_refusal(outcome):
    """Whether an outcome names a refused query rather than a value inside one.

    Worth a function rather than a bare ``startswith`` at each call site: it is also
    the test for "this row's text is adversarial by construction", which is the thing
    a reader must not get wrong.
    """
    return outcome.startswith(REFUSED_PREFIX)


# Longest stored form of a key and of free text. The search route caps neither — its
# ``q`` is ``Field(min_length=2)`` with no maximum — so without this a single large
# payload would set the size of a document that is otherwise fixed by design.
KEY_MAX = 200
TEXT_MAX = 500

# C0 and C1 control characters. ESC is the one that matters — remove it and an ANSI
# sequence is inert, since what remains ("[31m") is ordinary visible text rather than an
# instruction to the terminal. Newline and tab go the same way: this is one-line text,
# and keeping them would let stored input forge line breaks in a reviewer's output.
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def _clean(text, limit):
    """Strip control characters, collapse whitespace, truncate to ``limit`` codepoints.

    Applied to every field that carries text the user typed. A reviewer reads this
    collection in a terminal, so escape sequences in stored input are not a theoretical
    concern — they are the one vector this data actually touches today.

    Control characters become spaces rather than disappearing: deleting them would glue
    the words on either side together ("instrucciones\\nsystem"), quietly changing the
    evidence. The whitespace collapse that follows puts it back to one space. Truncation
    is by codepoint (Python slicing), so it cannot cut a character in half.
    """
    if text is None:
        return None
    return " ".join(_CONTROL.sub(" ", text).split())[:limit]


class SearchDiagnosticEvent(DocBase):
    """One thing one search could not do: an unidentified (or arbitrarily identified)
    value, or a refusal of the whole query.

    ``extra="forbid"`` even though this never comes from a request: it is assembled by
    hand at the call site, and a typo in a field name would otherwise be stored as a
    brand-new field and noticed by nobody.
    """

    model_config = ConfigDict(extra="forbid")

    # Which filter the value was meant to fill ("mentions", "speaker", "entities") and
    # the canonical form of the value, which is what groups sightings together. The
    # caller derives the key with the same normalisation the resolver itself uses, so a
    # key here means the same thing it means in the search path.
    #
    # A refusal has no field and no value in that sense — it is a verdict on the whole
    # query — so it is filed under the literal field ``"query"`` with the normalised
    # query text as its key.
    field: str
    key: str
    outcome: str
    # The surface form exactly as the query carried it. Kept verbatim because deciding
    # that two surfaces mean the same person is a judgement call made at review time,
    # not something the writer can settle: "Rueda" and "Alfonso Rueda" normalise apart,
    # and no automatic rule can join them without also joining two different Ruedas.
    # For a refusal it is the query itself, which is the evidence the gate fired on.
    value: str
    # True when the miss made the query unsatisfiable, i.e. a real person got zero
    # results. This is the priority ordering for a curation round.
    #
    # A refusal is deliberately NOT blocking, however little the user got back: this
    # counter sorts what curation should fix next, and a refused injection is not a gap
    # in any catalog. Letting junk head that list would make the sort useless.
    blocking: bool = False
    # The resolver's own hint, and the most useful field here: absent means nobody in the
    # catalog is close (a genuinely unknown person), "'X' (87)" means X exists but the
    # spelling did not reach the threshold (an alias gap), and "ambiguous: 'X' / 'Y'"
    # means the resolver refused a tie. Always absent on a refusal — nothing was resolved.
    suggestion: str | None = None
    # ``AMBIGUOUS`` only: who won the tie, and everyone who was in it.
    chosen: str | None = None
    tied: list[str] = Field(default_factory=list)
    # ``refused_unsupported_language`` only: the language the parser read the query as.
    # Its own field rather than a reuse of ``suggestion``, whose documented meaning
    # ("absent means nobody in the catalog is close") would otherwise depend on which
    # outcome you were looking at.
    language: str | None = None
    # Context for adjudication. The topic and filters say what the query was ABOUT, which
    # is often what tells you which of two same-named people was meant. Both are absent on
    # a refusal, which is refused before anything is resolved.
    query: str
    semantic_query: str | None = None
    filters: dict = Field(default_factory=dict)
    # Which parser produced this reading. An empty string is a legitimate value meaning
    # "no model was pinned, the provider default decided" — not missing data.
    parser_model: str | None = None
    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Sanitising here rather than at the call site so it cannot be skipped: every writer
    # goes through this model, and a future one should not have to remember.
    @field_validator("key")
    @classmethod
    def _clean_key(cls, value):
        return _clean(value, KEY_MAX)

    @field_validator("value", "query", "semantic_query")
    @classmethod
    def _clean_text(cls, value):
        return _clean(value, TEXT_MAX)


class SearchDiagnostic(DocBase):
    """The aggregate the repository maintains — one per ``(field, key, outcome)``.

    Read side only; nothing writes this model. Three of its fields are worth knowing
    about when reviewing:

    ``suggestions`` accumulates every distinct hint ever seen, so it doubles as a record
    of our own changes: a row whose hints go from nothing to "'X' (87)" is a row where a
    catalog entry landed underneath it. And more than one value in ``chosen`` is proof
    that an ``AMBIGUOUS`` row is genuinely unstable — the tie is decided by the order of
    a set, so the same query can resolve to a different person after a restart. More than
    one value in ``languages`` means the parser read the same refused query as two
    different languages, which says the reading is unreliable rather than that the user
    changed language.

    ``counts_by_month`` is what answers "is this still a gap": if the month after a fix
    never appears, the row is done. On a refusal row it answers a different question —
    whether a gate is still being tripped, and how hard.
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
    languages: list[str] = Field(default_factory=list)
    examples: list[dict] = Field(default_factory=list)
    first_seen: datetime | None = None
    last_seen: datetime | None = None

    @property
    def refused(self):
        """True when this row is a refused query — and therefore holds hostile text."""
        return is_refusal(self.outcome)

    def __str__(self):
        return f"{self.field}:{self.key} ×{self.count} ({self.outcome})"
