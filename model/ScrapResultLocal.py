from pydantic import BaseModel


# ==============================================
# =            Template Data Types             =
# ==============================================
class GenderTemplateDataLocal(BaseModel):
    genderDiversityIndex: float


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
    partyDiversityIndex: float
