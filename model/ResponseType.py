from pydantic import BaseModel
from typing import TypeVar, Generic


class LocalInfo(BaseModel):
    name: str
    id: int


class RegionInfo(BaseModel):
    name: str
    id: int
    local: list[LocalInfo]


class PartyInfo(BaseModel):
    name: str
    color: int

    model_config = {"json_schema_extra": {"example": {"name": "정상이당", "count": 10}}}


class Diversity(BaseModel):
    action_type: str
    value: float

    model_config = {
        "json_schema_extra": {"example": {"action_type": "gender", "value": 0.5}}
    }


class AgeInfo(BaseModel):
    minAge: int
    maxAge: int
    count: int

    model_config = {
        "json_schema_extra": {"example": {"minAge": 10, "maxAge": 20, "count": 10}}
    }


class PartyInfo(BaseModel):
    party: str
    count: int

    model_config = {"json_schema_extra": {"example": {"party": "숭구리당당", "count": 10}}}


class GenderInfo(BaseModel):
    gender: str
    count: int

    model_config = {"json_schema_extra": {"example": {"gender": "male", "count": 10}}}


T = TypeVar("T", GenderInfo, PartyInfo, AgeInfo)


class ChartResponse(BaseModel, Generic[T]):
    data: list[T]

    model_config = {
        "json_schema_extra": {"example": {"data": [{"gender": "male", "count": 10}]}}
    }
