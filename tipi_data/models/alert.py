from datetime import datetime

from pydantic import Field

from tipi_data.models.base import DynamicEmbeddedModel, DynamicModel, MongoModel


class Search(DynamicEmbeddedModel):
    hash: str | None = None
    search: str | None = None
    dbsearch: str | None = None
    created: datetime | None = None
    validated: bool = False
    validation_email_sent: bool | None = None
    validation_email_sent_date: datetime | None = None

    def __str__(self):
        return self.hash


class Alert(MongoModel):
    email: str | None = None
    searches: list[Search] = Field(default_factory=list)

    def __str__(self):
        return self.email


class InitiativeAlert(DynamicModel):
    pass
