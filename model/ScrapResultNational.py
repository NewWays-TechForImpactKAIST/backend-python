from pydantic import BaseModel


# ==============================================
# =            Template Data Types             =
# ==============================================
class GenderTemplateDataNational(BaseModel):
    genderDiversityIndex: float


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
    partyDiversityIndex: float
