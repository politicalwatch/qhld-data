from tipi_data import db
from tipi_data.models.session import Session


class Sessions:
    @staticmethod
    def save(session: Session):
        """Upsert a sitting, accumulating its ``references`` roster.

        Speeches are extracted per initiative ``reference``, so the same sitting is
        written once per debate it hosts. A plain ``replace_one`` would reset the
        roster to the single reference of the current run; instead we ``$set`` the
        (stable) metadata and ``$addToSet`` the references, so the roster grows as
        more of the sitting's debates are extracted."""
        doc = session.to_bson()
        references = doc.pop("references", [])
        doc.pop("_id", None)
        update = {"$set": doc}
        if references:
            update["$addToSet"] = {"references": {"$each": references}}
        return db.sessions.update_one({"_id": session.id}, update, upsert=True)
