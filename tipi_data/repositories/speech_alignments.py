from tipi_data import DoesNotExist, db
from tipi_data.models.speech_alignment import SpeechAlignment, track_id


class SpeechAlignments:
    """Subtitle cue tracks, one document per block of a speech.

    Every read here is a lookup by ``_id``, single or ``$in``, which is why the
    collection carries no index of its own: the caller always knows a speech's blocks
    from ``Speech.speech``, so it never has to search for them.

    A block is named by its language AND its role, because the language alone does not
    identify one: a mostly-Spanish speech whose co-official passage the Diario also
    printed in Spanish has two blocks that are both ``es``. So every method here takes
    ``original`` beside ``lang``, defaulting to the as-delivered block — the only one a
    monolingual speech has.
    """

    @staticmethod
    def get(speech_id, lang, original=True):
        doc = db.speech_alignments.find_one(
            {"_id": track_id(speech_id, lang, original)})
        if doc is None:
            raise DoesNotExist(f"Speech {speech_id} has no {lang} alignment")
        return SpeechAlignment.model_validate(doc)

    @staticmethod
    def exists(speech_id, lang, original=True):
        """Whether one block of a speech is already aligned — what an incremental
        run skips on, without paying to deserialize the cue list."""
        return db.speech_alignments.count_documents(
            {"_id": track_id(speech_id, lang, original)}, limit=1) == 1

    @staticmethod
    def summary(speech_id, lang, original=True):
        """Everything about one track except its cues, or ``None``.

        What a page needs to say whether a speech has subtitles — the language to
        label the track with, and the fingerprint to check the cues still describe
        the transcript as stored. The cue list is the whole weight of the document
        (~9 KB against a couple of hundred bytes) and none of it is needed to answer
        that, so it is projected away rather than deserialized and discarded.

        A plain dict on purpose: this is deliberately *not* a ``SpeechAlignment``,
        and one with an empty ``cues`` would be indistinguishable from an alignment
        that timed nothing.
        """
        return db.speech_alignments.find_one(
            {"_id": track_id(speech_id, lang, original)}, {"cues": 0})

    @staticmethod
    def summaries(speech_id, blocks):
        """The cue-less summary of each of ``blocks`` that exists, in that order.

        ``blocks`` is ``[(lang, original)]``, as a speech lists them. One round trip for
        the whole question "what can this page offer", rather than one per block. A block
        with no track is simply absent from the result, so the caller learns which exist
        by what comes back.
        """
        wanted = [track_id(speech_id, lang, original) for lang, original in blocks]
        found = {doc["_id"]: doc for doc in db.speech_alignments.find(
            {"_id": {"$in": wanted}}, {"cues": 0})}
        return [found[key] for key in wanted if key in found]

    @staticmethod
    def save(alignment: SpeechAlignment):
        """Replace the whole document.

        ``replace_one`` rather than the ``$set``/``$addToSet`` of ``Speeches.save``:
        an alignment is derived wholly from one audio file and one block of text, so
        a re-run supersedes its predecessor instead of accumulating with it. Because
        the key names the block too, re-aligning one block of a speech cannot disturb
        its sibling.
        """
        return db.speech_alignments.replace_one(
            {"_id": alignment.id}, alignment.to_bson(), upsert=True)

    @staticmethod
    def delete(speech_id, lang, original=True):
        return db.speech_alignments.delete_one(
            {"_id": track_id(speech_id, lang, original)})

    @staticmethod
    def delete_all(speech_id, blocks):
        """Drop every track of a speech — what a re-extraction that changed the
        language split has to do, since a block that no longer exists would otherwise
        leave a track nothing ever reads or supersedes."""
        return db.speech_alignments.delete_many(
            {"_id": {"$in": [track_id(speech_id, lang, original)
                             for lang, original in blocks]}})
