import re
from datetime import datetime

from tipi_data.models.footprint import FootprintByDeputy
from tipi_data.schemas.base import BaseSchema, FootprintElementOut


def transform_dates(text):
    REGEX = re.compile(
        r"[A-Z][a-z]{1,2}\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dev)\s(\d{2})\s00:00:00\sCES?T\s(\d{4})"
    )
    MONTHS = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
        "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
        "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
    }
    results = REGEX.finditer(text)
    for result in results:
        full_date = result.group(0)
        month = result.group(1)
        day = result.group(2)
        year = result.group(3)
        new_date = day + "/" + MONTHS[month] + "/" + year
        text = text.replace(full_date, new_date)
    return text


def _footprint(deputy_id):
    """Per-deputy footprint lookup. Preserves the original N+1 behavior
    (one query per serialized deputy); returns (score, topics)."""
    try:
        fbd = FootprintByDeputy.objects.get(id=deputy_id)
        topics = [FootprintElementOut.model_validate(t) for t in fbd.topics]
        return fbd.score, topics
    except Exception:
        return 0.0, []


class DeputySchema(BaseSchema):
    # marshmallow load_only -> excluded: email, web, twitter, facebook,
    # public_position, legislatures, party_logo, bio, start_date, end_date, url, extra
    id: str
    name: str | None = None
    parliamentarygroup: str | None = None
    image: str | None = None
    birthdate: datetime | None = None
    age: int | None = None
    gender: str | None = None
    constituency: str | None = None
    party_name: str | None = None
    active: bool | None = None
    footprint: float | None = None
    footprint_by_topics: list[FootprintElementOut] = []

    @classmethod
    def from_doc(cls, obj):
        score, topics = _footprint(obj.id)
        return cls(
            id=obj.id,
            name=obj.name,
            parliamentarygroup=obj.parliamentarygroup,
            image=obj.image,
            birthdate=obj.birthdate,
            age=obj.age,
            gender=obj.gender,
            constituency=obj.constituency,
            party_name=obj.party_name,
            active=obj.active,
            footprint=score,
            footprint_by_topics=topics,
        )


class DeputyExtendedSchema(BaseSchema):
    # marshmallow load_only -> excluded: start_date, end_date
    id: str
    name: str | None = None
    parliamentarygroup: str | None = None
    image: str | None = None
    email: str | None = None
    web: str | None = None
    twitter: str | None = None
    facebook: str | None = None
    birthdate: datetime | None = None
    age: int | None = None
    gender: str | None = None
    constituency: str | None = None
    public_position: list[str] = []
    bio: list[str] = []
    legislatures: list[str] = []
    party_logo: str | None = None
    party_name: str | None = None
    url: str | None = None
    active: bool | None = None
    extra: dict | None = None
    footprint: float | None = None
    footprint_by_topics: list[FootprintElementOut] = []

    @classmethod
    def from_doc(cls, obj):
        score, topics = _footprint(obj.id)
        public_position = [transform_dates(p) for p in (obj.public_position or [])]
        extra = _transform_extra(obj.extra)
        return cls(
            id=obj.id,
            name=obj.name,
            parliamentarygroup=obj.parliamentarygroup,
            image=obj.image,
            email=obj.email,
            web=obj.web,
            twitter=obj.twitter,
            facebook=obj.facebook,
            birthdate=obj.birthdate,
            age=obj.age,
            gender=obj.gender,
            constituency=obj.constituency,
            public_position=public_position,
            bio=list(obj.bio or []),
            legislatures=list(obj.legislatures or []),
            party_logo=obj.party_logo,
            party_name=obj.party_name,
            url=obj.url,
            active=obj.active,
            extra=extra,
            footprint=score,
            footprint_by_topics=topics,
        )


class DeputyCompactSchema(BaseSchema):
    # Same exposed fields as DeputySchema MINUS footprint (no per-row query).
    id: str
    name: str | None = None
    parliamentarygroup: str | None = None
    image: str | None = None
    birthdate: datetime | None = None
    age: int | None = None
    gender: str | None = None
    constituency: str | None = None
    party_name: str | None = None
    active: bool | None = None


def _transform_extra(extra):
    """Mirror of the old ExtraField: transform the date keys of
    ``extra['declarations']``. Guarded against a missing 'declarations' key
    (the original would KeyError)."""
    if not extra:
        return extra
    declarations = extra.get("declarations")
    if not declarations:
        return extra
    new_declarations = {}
    for declaration, link in declarations.items():
        new_declarations[transform_dates(declaration)] = link
    extra = dict(extra)
    extra["declarations"] = new_declarations
    return extra
