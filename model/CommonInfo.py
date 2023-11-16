from pydantic import BaseModel


class LocalInfo(BaseModel):
    name: str
    id: int


class RegionInfo(BaseModel):
    name: str
    id: int
    local: list[LocalInfo]


class PartyInfo(BaseModel):
    name: str
    color: str
