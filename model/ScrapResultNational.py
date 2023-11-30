from pydantic import BaseModel


# ==============================================
# =            Template Data Types             =
# ==============================================
class GenderTemplateDataNational(BaseModel):
    class GenderTemplateDataPoint(BaseModel):
        year: int
        malePop: int
        femalePop: int

    genderDiversityIndex: float
    current: GenderTemplateDataPoint
    currentCandidate: GenderTemplateDataPoint
    prev: GenderTemplateDataPoint
    prevCandidate: GenderTemplateDataPoint


class AgeTemplateDataNational(BaseModel):
    class AgeRankingParagraphData(BaseModel):
        ageDiversityIndex: float

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
        year: int
        candidateCount: int
        electedCount: int
        firstQuintile: int
        lastQuintile: int

    rankingParagraph: AgeRankingParagraphData
    indexHistoryParagraph: AgeIndexHistoryParagraphData
    ageHistogramParagraph: AgeHistogramParagraphData


class PartyTemplateDataNational(BaseModel):
    class PartyCountDataPoint(BaseModel):
        party: str
        count: int

    partyDiversityIndex: float
    prevElected: list[PartyCountDataPoint]
    currentElected: list[PartyCountDataPoint]
    currentCandidate: list[PartyCountDataPoint]
