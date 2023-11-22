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
                {"ageDiversityIndex": age_diversity_index}
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
