"""Where each subtitle line of a speech falls in its video.

**One document per block of a speech**, keyed by ``f"{speech_id}:{lang}:{role}"``.
Produced by forced alignment of the Diario transcript against the intervention's own
video cut, so the words are the stenographers' and only the timing comes from a model.

Two things are deliberately *not* stored. There is no subtitle text: a cue carries
character offsets into the speech block it was aligned against, and the text is
sliced out of ``Speech.speech[].text`` when a WebVTT track is rendered — so the
subtitles cannot drift from the transcript, and the document stays small enough to
be uninteresting. And there is no WebVTT file: the format is a projection of these
numbers, rendered on demand.

A co-official-language speech is published as the original followed by its full
Spanish interpretation, and **both are timed against the same audio**. The
translation's words are not the ones spoken, but a CTC aligner only has to find a
monotone path through the clip and Spanish, Catalan and Galician are close enough
that it finds the right one — measured at a median error of 0 ms against the
as-delivered track on shared anchors. That matters because most readers only read
Spanish, so without this a Galician intervention would offer them a Galician track.

Why per-block documents rather than one document holding several tracks: a track is
derived wholly from one audio file and one block of text, so re-aligning one block must
supersede exactly that block and leave its sibling untouched — which is what the
whole-document ``replace_one`` in the repository expresses. The composite key also keeps
every read a lookup by ``_id``: a caller knows a speech's blocks from ``Speech.speech``,
so "which tracks does this speech have" is an ``$in`` over at most a couple of ids and
still needs no index.

**The language alone does not identify a block.** A speech mostly given in Spanish, one
passage of which the Diario also printed in Spanish, has two blocks that are both ``es``
— what separates them is the role each plays, which is exactly what ``original`` records.
So the key names both, and a track is asked for as a language *and* a role.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from tipi_data.models.base import MongoModel


def track_id(speech_id, lang, original=True):
    """The ``_id`` of one speech's track for one block.

    A function rather than an f-string at each call site because the writer and every
    reader have to agree on it exactly, the same reason the text fingerprint is taken
    through one function on both ends of its guard.

    ``original`` is the block's own flag: what was delivered, or the Diario's rendering
    of it. It is part of the key because a language is not enough to tell two blocks
    apart — see the note above — and it is spelled out rather than encoded as a flag so
    an id read in the shell says what it is.
    """
    return f"{speech_id}:{lang}:{'original' if original else 'translation'}"


class Cue(BaseModel):
    """One subtitle line: when it is spoken, and which characters of the speech
    block it covers.

    The offsets are into the block's stored text *including* the stenographers'
    parenthesized annotations, because that is the string the transcript is
    rendered from and the string search highlights are located in. Alignment skips
    the annotations; the offsets still span them."""

    start_ms: int
    end_ms: int
    char_start: int
    char_end: int


class SpeechAlignment(MongoModel):
    """One language's cue track for one speech. ``_id`` is ``track_id(speech_id, lang)``."""

    # Carried as a field as well as inside the key: a document that only spelled its
    # speech into its ``_id`` would be unreadable in the shell and unjoinable in an
    # aggregation. Not queried on, so it needs no index.
    speech_id: str
    # Which block of ``Speech.speech`` the offsets index, by language and position.
    lang: str
    block_index: int
    # Whether the Diario marks this block as delivered. What separates a track timed
    # against the words actually spoken from one timed against their translation — the
    # reader is told which they are watching, since the second is a derived artifact
    # even though its timings are measured.
    original: bool = True
    cues: list[Cue] = Field(default_factory=list)
    # The drift guard, and the reason this document is safe without stored text.
    # Offsets into a transcript that has since changed are not stale but silently
    # WRONG, so a reader must compare these against the block it is about to slice
    # and treat a mismatch as "re-align", never as "serve anyway".
    text_sha256: str
    text_length: int
    # Which artifact produced the timings. Recorded per alignment because the model
    # is fetched from a third-party conversion pinned by revision: if those bytes
    # ever change underneath us, the alignments made before and after are
    # distinguishable instead of merely suspicious.
    model_id: str | None = None
    model_revision: str | None = None
    model_sha256: str | None = None
    # The trust gate: the audio under a sample of cues is decoded and compared to
    # the text those cues claim, and ``score`` is the mean similarity. Stored and
    # served either way — a low score flags an alignment for review, it does not
    # withhold it, because the check shares the acoustic model's blind spots and
    # reports false alarms in passages whose timings are in fact correct.
    #
    # It is NOT comparable between an as-delivered track and a translated one. The
    # check asks whether the audio says these words, and a Spanish translation over
    # Galician audio does not, however exactly its timings land: measured at 80 where
    # the same cues agreed with the as-delivered track to the millisecond. So never
    # rank the two kinds against each other, and never gate one on the other's floor.
    score: float | None = None
    verdict: str | None = None
    audio_seconds: float | None = None
    # Aware UTC, as in SearchRating: the client is not ``tz_aware``, so this reads
    # back naive UTC and the caller rendering it is the one to say so.
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))

    def __str__(self):
        return f"{self.id} {len(self.cues)} cues ({self.lang})"
