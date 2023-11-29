from pydantic import BaseModel


# ==============================================
# =            Template Data Types             =
# ==============================================
class GenderTemplateDataLocal(BaseModel):
    class GenderTemplateDataPoint(BaseModel):
        year: int
        malePop: int
        femalePop: int

    metroId: int
    localId: int
    genderDiversityIndex: float
    current: GenderTemplateDataPoint
    prev: GenderTemplateDataPoint
    meanMalePop: float
    meanFemalePop: float


class AgeTemplateDataLocal(BaseModel):
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


class PartyTemplateDataLocal(BaseModel):
    class PartyCountDataPoint(BaseModel):
        party: str
        count: int

    metroId: int
    localId: int
    partyDiversityIndex: float
    prevElected: list[PartyCountDataPoint]
    currentElected: list[PartyCountDataPoint]
    currentCandidate: list[PartyCountDataPoint]
