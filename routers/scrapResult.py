from fastapi import APIRouter
from model import BasicResponse, MongoDB, ScrapResult
from utils import diversity
from typing import TypeVar

router = APIRouter("/localCouncil", tags=["localCouncil"])

AGE_STAIR = 10


@router.get("/template-data/{metroId}/{localId}")
async def getLocalTemplateData(
    metroId: int, localId: int, factor: ScrapResult.FactorType
) -> BasicResponse.ErrorResponse | ScrapResult.SexTemplateData | ScrapResult.AgeTemplateData | ScrapResult.PartyTemplateData:
    if (
        await MongoDB.client.district_db["local_district"].find_one(
            {"local_id": localId, "metro_id": metroId}
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

    councilors = MongoDB.client.council_db["local_councilor"].find(
        {"local_id": localId}
    )

    match factor:
        case ScrapResult.FactorType.sex:
            sex_list = [councilor["sex"] async for councilor in councilors]
            sex_diversity_index = diversity.gini_simpson(sex_list)
            return ScrapResult.SexTemplateData.model_validate(
                {"sexDiversityIndex": sex_diversity_index}
            )

        case ScrapResult.FactorType.age:
            age_list = [councilor["age"] async for councilor in councilors]
            age_diversity_index = diversity.gini_simpson(age_list, stair=AGE_STAIR)
            return ScrapResult.AgeTemplateData.model_validate(
                {"ageDiversityIndex": age_diversity_index}
            )

        case ScrapResult.FactorType.party:
            party_list = [councilor["party"] async for councilor in councilors]
            party_diversity_index = diversity.gini_simpson(party_list)
            return ScrapResult.PartyTemplateData.model_validate(
                {"partyDiversityIndex": party_diversity_index}
            )


T = TypeVar("T", ScrapResult.SexChartData, ScrapResult.AgeChartData, ScrapResult.PartyChartData)

@router.get("/chart-data/{metroId}/{localId}")
async def getLocalChartData(
    metroId: int, localId: int, factor: ScrapResult.FactorType
) -> BasicResponse.ErrorResponse | ScrapResult.ChartData[T]:
    if (
        await MongoDB.client.district_db["local_district"].find_one(
            {"local_id": localId, "metro_id": metroId}
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

    councilors = MongoDB.client.council_db["local_councilor"].find(
        {"local_id": localId}
    )

    match factor:
        case ScrapResult.FactorType.sex:
            sex_list = [councilor["sex"] async for councilor in councilors]
            sex_count = diversity.count(sex_list)
            return ScrapResult.ChartData[ScrapResult.SexChartDataPoint].model_validate(
                {"data": [{"sex": sex, "count": sex_count[sex]} for sex in sex_count]}
            )

        case ScrapResult.FactorType.age:
            age_list = [councilor["age"] async for councilor in councilors]
            age_count = diversity.count(age_list, stair=AGE_STAIR)
            return ScrapResult.ChartData[ScrapResult.AgeChartDataPoint].model_validate(
                {
                    "data": [
                        {
                            "minAge": age,
                            "maxAge": age + AGE_STAIR - 1,
                            "count": age_count[age],
                        }
                        for age in age_count
                    ]
                }
            )

        case ScrapResult.FactorType.party:
            party_list = [councilor["party"] async for councilor in councilors]
            party_count = diversity.count(party_list)
            return ScrapResult.ChartData[ScrapResult.PartyChartDataPoint].model_validate(
                {
                    "data": [
                        {"party": party, "count": party_count[party]}
                        for party in party_count
                    ]
                }
            )
