"""Where each subtitle line of a speech falls in its video.

One document per speech, keyed by the speech ``_id``. Produced by forced alignment
of the Diario transcript against the intervention's own video cut, so the words are
the stenographers' and only the timing comes from a model.

Two things are deliberately *not* stored. There is no subtitle text: a cue carries
character offsets into the speech block it was aligned against, and the text is
sliced out of ``Speech.speech[].text`` when a WebVTT track is rendered — so the
subtitles cannot drift from the transcript, and the document stays small enough to
be uninteresting. And there is no WebVTT file: the format is a projection of these
numbers, rendered on demand.

Only the as-delivered block is alignable. A co-official-language speech is
published as the original followed by its full Spanish interpretation, and the
audio corresponds to the original alone — hence ``lang``/``block_index``, which say
which block the offsets belong to.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from tipi_data.models.base import MongoModel


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
    """The cue track of one speech. ``_id`` is the ``Speech._id``."""

    # Which block of ``Speech.speech`` the offsets index, by language and position.
    lang: str
    block_index: int
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
    score: float | None = None
    verdict: str | None = None
    audio_seconds: float | None = None
    # Aware UTC, as in SearchRating: the client is not ``tz_aware``, so this reads
    # back naive UTC and the caller rendering it is the one to say so.
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))

    def __str__(self):
        return f"{self.id} {len(self.cues)} cues ({self.lang})"
