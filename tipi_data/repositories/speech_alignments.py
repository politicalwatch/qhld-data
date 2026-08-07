from tipi_data import DoesNotExist, db
from tipi_data.models.speech_alignment import SpeechAlignment


class SpeechAlignments:
    @staticmethod
    def get(id):
        doc = db.speech_alignments.find_one({"_id": id})
        if doc is None:
            raise DoesNotExist(f"Speech {id} has no alignment")
        return SpeechAlignment.model_validate(doc)

    @staticmethod
    def exists(id):
        """Whether a speech is already aligned — what an incremental run skips on,
        without paying to deserialize the cue list."""
        return db.speech_alignments.count_documents({"_id": id}, limit=1) == 1

    @staticmethod
    def save(alignment: SpeechAlignment):
        """Replace the whole document.

        ``replace_one`` rather than the ``$set``/``$addToSet`` of ``Speeches.save``:
        an alignment is derived wholly from one audio file and one block of text, so
        a re-run supersedes its predecessor instead of accumulating with it.
        """
        return db.speech_alignments.replace_one(
            {"_id": alignment.id}, alignment.to_bson(), upsert=True)

    @staticmethod
    def delete(id):
        return db.speech_alignments.delete_one({"_id": id})
