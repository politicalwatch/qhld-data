from tipi_data.schemas.base import BaseSchema


class TotalsVotesOut(BaseSchema):
    present: int | None = None
    skip: int | None = None
    yes: int | None = None
    no: int | None = None
    abstention: int | None = None


class ByDeputyOut(BaseSchema):
    name: str | None = None
    seat: str | None = None
    group: str | None = None
    vote: str | None = None


class GroupVoteOut(BaseSchema):
    yes: int | None = None
    no: int | None = None
    abstention: int | None = None
    skip: int | None = None


class ByGroupOut(BaseSchema):
    name: str | None = None
    votes: GroupVoteOut | None = None


class VotingSchema(BaseSchema):
    # ``Voting`` is a mongoengine DynamicDocument, but the previous
    # marshmallow-mongoengine schema only serialized declared fields, so we keep
    # parity by declaring those and not exposing per-document dynamic extras.
    id: str
    reference: str | None = None
    title: str | None = None
    subgroup_text: str | None = None
    subgroup_title: str | None = None
    totals: TotalsVotesOut | None = None
    by_deputies: list[ByDeputyOut] = []
    by_groups: list[ByGroupOut] = []
