from pydantic import Field

from tipi_data.models.base import DynamicModel, DocBase


class TotalsVotes(DocBase):
    present: int | None = None
    skip: int | None = None
    yes: int | None = None
    no: int | None = None
    abstention: int | None = None


class ByDeputy(DocBase):
    name: str | None = None
    seat: str | None = None
    group: str | None = None
    vote: str | None = None


class GroupVote(DocBase):
    yes: int = 0
    no: int = 0
    abstention: int = 0
    skip: int = 0


class ByGroup(DocBase):
    name: str | None = None
    votes: GroupVote | None = None


class Voting(DynamicModel):
    reference: str | None = None
    title: str | None = None
    subgroup_text: str | None = None
    subgroup_title: str | None = None
    totals: TotalsVotes | None = None
    by_deputies: list[ByDeputy] = Field(default_factory=list)
    by_groups: list[ByGroup] = Field(default_factory=list)
