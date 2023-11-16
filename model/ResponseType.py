from pydantic import BaseModel
from typing import TypeVar, Generic

class LocalInfo(BaseModel):
    name : str
    id : int

class RegionInfo(BaseModel):
    name : str
    id : int
    local: list[LocalInfo]

class PartyInfo(BaseModel):
    name : str
    color : int

class Diversity(BaseModel):
    action_type : str
    value : float

class AgeInfo(BaseModel):
    minAge: int
    maxAge: int
    count: int

class PartyInfo(BaseModel):
    party : str
    count : int

class SexInfo(BaseModel):
    sex: str
    count: int

T = TypeVar("T", SexInfo, PartyInfo, AgeInfo)

class ChartResponse(BaseModel, Generic[T]):
    data : list[T]
