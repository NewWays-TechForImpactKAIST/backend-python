from fastapi import APIRouter
from model import BasicResponse, MongoDB, ScrapResult
from utils import diversity
from typing import TypeVar


router = APIRouter(prefix="/localCouncil", tags=["localCouncil"])

AGE_STAIR = 10


@router.get("/template-data/{metroId}/{localId}")
async def getLocalTemplateData(
    metroId: int, localId: int, factor: ScrapResult.FactorType
) -> BasicResponse.ErrorResponse | ScrapResult.GenderTemplateData | ScrapResult.AgeTemplateData | ScrapResult.PartyTemplateData:
    if (
        await MongoDB.client.district_db["local_district"].find_one(
            {"localId": localId, "metroId": metroId}
        )
        is None
    ):
        return BasicResponse.ErrorResponse.model_validate(
            {
                "error": "RegionCodeError",
                "code": BasicResponse.REGION_CODE_ERR,
                "message": f"No local district with metroId {metroId} and localId {localId}.",
            }
        )

    councilors = MongoDB.client.council_db["local_councilor"].find({"localId": localId})

    match factor:
        case ScrapResult.FactorType.gender:
            gender_list = [councilor["gender"] async for councilor in councilors]
            gender_diversity_index = diversity.gini_simpson(gender_list)
            return ScrapResult.GenderTemplateData.model_validate(
                {"genderDiversityIndex": gender_diversity_index}
            )

        case ScrapResult.FactorType.age:
            age_list = [councilor["age"] async for councilor in councilors]
            age_diversity_index = diversity.gini_simpson(age_list, stair=AGE_STAIR)
            return ScrapResult.AgeTemplateData.model_validate(
                {
                    "metroId": metroId,
                    "localId": localId,
                    "rankingParagraph": {
                        "ageDiversityIndex": age_diversity_index,
                        "allIndices": [
                            {"metroId": 3, "rank": 2, "ageDiversityIndex": 0.9},
                            {"metroId": 14, "rank": 7, "ageDiversityIndex": 0.4},
                            {"metroId": 15, "rank": 18, "ageDiversityIndex": 0.2},
                        ],
                    },
                    "indexHistoryParagraph": {
                        "mostRecentYear": 2022,
                        "history": [
                            {
                                "year": 2022,
                                "unit": 8,
                                "candidateCount": 80,
                                "candidateDiversityIndex": 0.11,
                                "candidateDiversityRank": 33,
                                "electedDiversityIndex": 0.42,
                                "electedDiversityRank": 12,
                            },
                            {
                                "year": 2018,
                                "unit": 7,
                                "candidateCount": 70,
                                "candidateDiversityIndex": 0.73,
                                "candidateDiversityRank": 3,
                                "electedDiversityIndex": 0.85,
                                "electedDiversityRank": 2,
                            },
                        ],
                    },
                    "ageHistogramParagraph": {
                        "year": 2022,
                        "candidateCount": 80,
                        "electedCount": 16,
                        "firstQuintile": 66,
                        "lastQuintile": 29,
                        "divArea": {
                            "localId": 172,
                            "firstQuintile": 43,
                            "lastQuintile": 21,
                        },
                        "uniArea": {
                            "localId": 63,
                            "firstQuintile": 84,
                            "lastQuintile": 56,
                        },
                    },
                }
            )

        case ScrapResult.FactorType.party:
            party_list = [councilor["jdName"] async for councilor in councilors]
            party_diversity_index = diversity.gini_simpson(party_list)
            return ScrapResult.PartyTemplateData.model_validate(
                {"partyDiversityIndex": party_diversity_index}
            )


T = TypeVar(
    "T",
    ScrapResult.GenderChartDataPoint,
    ScrapResult.AgeChartDataPoint,
    ScrapResult.PartyChartDataPoint,
)


@router.get("/chart-data/{metroId}/{localId}")
async def getLocalChartData(
    metroId: int, localId: int, factor: ScrapResult.FactorType
) -> BasicResponse.ErrorResponse | ScrapResult.ChartData[T]:
    if (
        await MongoDB.client.district_db["local_district"].find_one(
            {"localId": localId, "metroId": metroId}
        )
        is None
    ):
        return BasicResponse.ErrorResponse.model_validate(
            {
                "error": "RegionCodeError",
                "code": BasicResponse.REGION_CODE_ERR,
                "message": f"No local district with metroId {metroId} and localId {localId}.",
            }
        )

    councilors = MongoDB.client.council_db["local_councilor"].find({"localId": localId})

    match factor:
        case ScrapResult.FactorType.gender:
            gender_list = [councilor["gender"] async for councilor in councilors]
            gender_count = diversity.count(gender_list)
            return ScrapResult.ChartData[
                ScrapResult.GenderChartDataPoint
            ].model_validate(
                {
                    "data": [
                        {"gender": gender, "count": gender_count[gender]}
                        for gender in gender_count
                    ]
                }
            )

        case ScrapResult.FactorType.age:
            age_list = [councilor["age"] async for councilor in councilors]
            age_count = diversity.count(age_list, stair=AGE_STAIR)
            return ScrapResult.ChartData[ScrapResult.AgeChartDataPoint].model_validate(
                {
                    "data": [
                        {
                            "minAge": age,
                            "maxAge": age + AGE_STAIR,
                            "count": age_count[age],
                        }
                        for age in age_count
                    ]
                }
            )

        case ScrapResult.FactorType.party:
            party_list = [councilor["jdName"] async for councilor in councilors]
            party_count = diversity.count(party_list)
            return ScrapResult.ChartData[
                ScrapResult.PartyChartDataPoint
            ].model_validate(
                {
                    "data": [
                        {"party": party, "count": party_count[party]}
                        for party in party_count
                    ]
                }
            )
