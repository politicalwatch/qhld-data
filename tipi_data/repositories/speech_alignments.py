from tipi_data import DoesNotExist, db
from tipi_data.models.speech_alignment import SpeechAlignment, track_id


class SpeechAlignments:
    """Subtitle cue tracks, one document per speech and language.

    Every read here is a lookup by ``_id``, single or ``$in``, which is why the
    collection carries no index of its own: the caller always knows which languages a
    speech could have from ``Speech.speech[].lang``, so it never has to search for them.
    """

    @staticmethod
    def get(speech_id, lang):
        doc = db.speech_alignments.find_one({"_id": track_id(speech_id, lang)})
        if doc is None:
            raise DoesNotExist(f"Speech {speech_id} has no {lang} alignment")
        return SpeechAlignment.model_validate(doc)

    @staticmethod
    def exists(speech_id, lang):
        """Whether one language of a speech is already aligned — what an incremental
        run skips on, without paying to deserialize the cue list."""
        return db.speech_alignments.count_documents(
            {"_id": track_id(speech_id, lang)}, limit=1) == 1

    @staticmethod
    def summary(speech_id, lang):
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
            {"_id": track_id(speech_id, lang)}, {"cues": 0})

    @staticmethod
    def summaries(speech_id, langs):
        """The cue-less summary of each of ``langs`` that exists, in that order.

        One round trip for the whole question "what can this page offer", rather than
        one per language. Languages with no track are simply absent from the result, so
        the caller learns which exist by what comes back.
        """
        wanted = [track_id(speech_id, lang) for lang in langs]
        found = {doc["_id"]: doc for doc in db.speech_alignments.find(
            {"_id": {"$in": wanted}}, {"cues": 0})}
        return [found[key] for key in wanted if key in found]

    @staticmethod
    def save(alignment: SpeechAlignment):
        """Replace the whole document.

        ``replace_one`` rather than the ``$set``/``$addToSet`` of ``Speeches.save``:
        an alignment is derived wholly from one audio file and one block of text, so
        a re-run supersedes its predecessor instead of accumulating with it. Because
        the key names the language too, re-aligning one language of a co-official
        speech cannot disturb the other.
        """
        return db.speech_alignments.replace_one(
            {"_id": alignment.id}, alignment.to_bson(), upsert=True)

    @staticmethod
    def delete(speech_id, lang):
        return db.speech_alignments.delete_one({"_id": track_id(speech_id, lang)})

    @staticmethod
    def delete_all(speech_id, langs):
        """Drop every track of a speech — what a re-extraction that changed the
        language split has to do, since a block that no longer exists would otherwise
        leave a track nothing ever reads or supersedes."""
        return db.speech_alignments.delete_many(
            {"_id": {"$in": [track_id(speech_id, lang) for lang in langs]}})
