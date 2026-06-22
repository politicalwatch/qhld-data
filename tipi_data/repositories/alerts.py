from tipi_data import db
from tipi_data.models.initiative import Initiative
from tipi_data.models.alert import Alert, InitiativeAlert


class Alerts():
    @staticmethod
    def get_all():
        return [Alert.model_validate(d) for d in db.alerts.find()]

    @staticmethod
    def get_validated():
        return [Alert.model_validate(d)
                for d in db.alerts.find({"searches.validated": True})]

    @staticmethod
    def get_with_unvalidated_searches():
        return [Alert.model_validate(d)
                for d in db.alerts.find({"searches.validated": False})]

    @staticmethod
    def save(alert: Alert):
        return db.alerts.replace_one(
            {"_id": alert.id}, alert.to_bson(), upsert=True)

    @staticmethod
    def remove_search(hash):
        # hash is unique per search, so pulling by hash across all matching
        # alerts is equivalent to the previous queryset-scoped pull.
        return db.alerts.update_many(
            {"searches.hash": hash},
            {"$pull": {"searches": {"hash": hash}}})

    @staticmethod
    def delete_empty():
        return db.alerts.delete_many({"searches": {"$size": 0}})


class InitiativeAlerts():
    @staticmethod
    def get_all():
        return [InitiativeAlert.model_validate(d)
                for d in db.initiatives_alerts.find()]

    @staticmethod
    def clear():
        db.initiatives_alerts.drop()

    @staticmethod
    def by_search(search, kb, exclude_fields=None):
        query = search
        query['tagged.knowledgebase'] = kb
        projection = {f: 0 for f in exclude_fields} if exclude_fields else None
        return [InitiativeAlert.model_validate(d)
                for d in db.initiatives_alerts.find(query, projection)]

    @staticmethod
    def create_alert(initiative: Initiative, reason: str = ''):
        prev = db.initiatives_alerts.find_one({"_id": initiative.id})
        if prev is not None:
            reason = prev.get('reason', reason)

        initiative_alert = InitiativeAlert(
                id=initiative.id,
                title=initiative.title,
                reference=initiative.reference,
                initiative_type=initiative.initiative_type,
                initiative_type_alt=initiative.initiative_type_alt,
                author_deputies=initiative.author_deputies,
                author_parliamentarygroups=initiative.author_parliamentarygroups,
                author_others=initiative.author_others,
                place=initiative.place,
                created=initiative.created,
                updated=initiative.updated,
                history=initiative.history,
                status=initiative.status,
                tagged=[t.model_dump() for t in initiative.tagged],
                url=initiative.url,
                extra=initiative.extra,
                reason=reason
                )
        try:
            db.initiatives_alerts.replace_one(
                {"_id": initiative_alert.id},
                initiative_alert.to_bson(),
                upsert=True,
            )
        except Exception:
            pass
