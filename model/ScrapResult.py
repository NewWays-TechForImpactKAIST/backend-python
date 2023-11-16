from pydantic import BaseModel
from enum import StrEnum


class SexType(StrEnum):
    male = "남"
    female = "여"


class FactorType(StrEnum):
    sex = "sex"
    age = "age"
    party = "party"


# ==============================================
# =            Template Data Types             =
# ==============================================
class SexTemplateData(BaseModel):
    sexDiversityIndex: float


class AgeTemplateData(BaseModel):
    ageDiversityIndex: float


class PartyTemplateData(BaseModel):
    partyDiversityIndex: float


# ==============================================
# =             Chart Data Types               =
# ==============================================
class SexChartDataPoint(BaseModel):
    sex: SexType
    count: int


class SexChartData(BaseModel):
    data: list[SexChartDataPoint]


class AgeChartDataPoint(BaseModel):
    minAge: int  # 닫힌 구간
    maxAge: int  # 닫힌 구간
    count: int


class AgeChartData(BaseModel):
    data: list[AgeChartDataPoint]


class PartyChartDataPoint(BaseModel):
    party: str
    count: int


class PartyChartData(BaseModel):
    data: list[PartyChartDataPoint]


# ==============================================
# =         Scrap Result Data Types            =
# ==============================================
class CouncilType(StrEnum):
    local_council = "local_council"
    national_council = "national_council"
    metropolitan_council = "metropolitan_council"
    local_leader = "local_leader"
    metro_leader = "metro_leader"


class CouncilInfo(BaseModel):
    name: str
    party: str


class ScrapResult(BaseModel):
    council_id: str
    council_type: CouncilType
    councilers: list[CouncilInfo]
