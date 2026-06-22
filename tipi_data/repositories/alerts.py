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


class InitiativeAlerts():
    @staticmethod
    def get_all():
        return [InitiativeAlert.model_validate(d)
                for d in db.initiatives_alerts.find()]

    @staticmethod
    def clear():
        db.initiatives_alerts.drop()

    @staticmethod
    def by_search(search, kb):
        query = search
        query['tagged.knowledgebase'] = kb
        return [InitiativeAlert.model_validate(d)
                for d in db.initiatives_alerts.find(query)]

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
