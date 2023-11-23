from pydantic import BaseModel
from enum import StrEnum
from typing import TypeVar, Generic


class GenderType(StrEnum):
    male = "남"
    female = "여"


class FactorType(StrEnum):
    gender = "gender"
    age = "age"
    party = "party"


# ==============================================
# =            Template Data Types             =
# ==============================================
class GenderTemplateData(BaseModel):
    genderDiversityIndex: float


class AgeTemplateData(BaseModel):
    class AgeRankingParagraphData(BaseModel):
        class AgeRankingAllIndices(BaseModel):
            localId: int
            rank: int
            ageDiversityIndex: float

        ageDiversityIndex: float
        allIndices: list[AgeRankingAllIndices]

    class AgeIndexHistoryParagraphData(BaseModel):
        class AgeIndexHistoryIndexData(BaseModel):
            year: int
            unit: int
            candidateCount: int
            candidateDiversityIndex: float
            candidateDiversityRank: int
            electedDiversityIndex: float
            electedDiversityRank: int

        mostRecentYear: int
        history: list[AgeIndexHistoryIndexData]

    class AgeHistogramParagraphData(BaseModel):
        class AgeHistogramAreaData(BaseModel):
            localId: int
            firstQuintile: int
            lastQuintile: int

        year: int
        candidateCount: int
        electedCount: int
        firstQuintile: int
        lastQuintile: int
        divArea: AgeHistogramAreaData
        uniArea: AgeHistogramAreaData

    metroId: int
    localId: int
    rankingParagraph: AgeRankingParagraphData
    indexHistoryParagraph: AgeIndexHistoryParagraphData
    ageHistogramParagraph: AgeHistogramParagraphData


class PartyTemplateData(BaseModel):
    partyDiversityIndex: float


# ==============================================
# =             Chart Data Types               =
# ==============================================
class GenderChartDataPoint(BaseModel):
    gender: GenderType
    count: int


class AgeChartDataPoint(BaseModel):
    minAge: int  # 닫힌 구간
    maxAge: int  # 열린 구간
    count: int


class PartyChartDataPoint(BaseModel):
    party: str
    count: int


T = TypeVar("T", GenderChartDataPoint, AgeChartDataPoint, PartyChartDataPoint)


class ChartData(BaseModel, Generic[T]):
    data: list[T]


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
