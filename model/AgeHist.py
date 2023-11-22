from pydantic import BaseModel
from enum import StrEnum


class AgeHistDataTypes(StrEnum):
    elected = "elected"
    candidate = "candidate"


class AgeHistMethodTypes(StrEnum):
    equal = "equal"
    kmeans = "kmeans"


class AgeHistDataPoint(BaseModel):
    minAge: int
    maxAge: int
    count: int
    ageGroup: int


class MetroAgeHistData(BaseModel):
    metroId: int
    data: list[AgeHistDataPoint]


class LocalAgeHistData(BaseModel):
    metroId: int
    localId: int
    data: list[AgeHistDataPoint]
