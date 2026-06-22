import datetime

from pydantic import Field

from tipi_data.models.base import MongoModel


class Deputy(MongoModel):
    name: str | None = None
    parliamentarygroup: str | None = None
    image: str | None = None
    email: str | None = None
    web: str | None = None
    twitter: str | None = None
    facebook: str | None = None
    birthdate: datetime.datetime | None = None
    age: int | None = None
    gender: str | None = None
    constituency: str | None = None
    public_position: list[str] = Field(default_factory=list)
    bio: list[str] = Field(default_factory=list)
    legislatures: list[str] = Field(default_factory=list)
    party_logo: str | None = None
    party_name: str | None = None
    start_date: datetime.datetime | None = None
    end_date: datetime.datetime | None = None
    url: str | None = None
    active: bool | None = None
    extra: dict = Field(default_factory=dict)

    def __str__(self):
        return self.name

    def calculate_age(self):
        if not self.birthdate:
            return
        today = datetime.datetime.today()
        years = today.year - self.birthdate.year
        if today.month < self.birthdate.month or \
                (today.month == self.birthdate.month and today.day < self.birthdate.day):
            years -= 1
        self.age = years

    def get_fullname(self):
        parts = self.name.split(',')
        name = parts[1] + ' ' + parts[0]
        return name.strip()
