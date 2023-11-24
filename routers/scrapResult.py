from typing import TypeVar
from fastapi import APIRouter
from model.BasicResponse import ErrorResponse, REGION_CODE_ERR
from model.MongoDB import client
from model.ScrapResult import (
    GenderTemplateData,
    GenderChartDataPoint,
    AgeTemplateData,
    AgeChartDataPoint,
    PartyTemplateData,
    PartyChartDataPoint,
    FactorType,
    ChartData,
)
from utils import diversity


router = APIRouter(prefix="/localCouncil", tags=["localCouncil"])

AGE_STAIR = 10


@router.get("/template-data/{metroId}/{localId}")
async def getLocalTemplateData(
    metroId: int, localId: int, factor: FactorType
) -> ErrorResponse | GenderTemplateData | AgeTemplateData | PartyTemplateData:
    if (
        await client.district_db["local_district"].find_one(
            {"localId": localId, "metroId": metroId}
        )
        is None
    ):
        return ErrorResponse.model_validate(
            {
                "error": "RegionCodeError",
                "code": REGION_CODE_ERR,
                "message": f"No local district with metroId {metroId} and localId {localId}.",
            }
        )

    local_stat = await client.stats_db["diversity_index"].find_one({"localId": localId})

    match factor:
        case FactorType.gender:
            return GenderTemplateData.model_validate(
                {"genderDiversityIndex": local_stat["genderDiversityIndex"]}
            )

        case FactorType.age:
            # ============================
            #      rankingParagraph
            # ============================
            age_diversity_index = local_stat["ageDiversityIndex"]

            localIds_of_same_metroId = [
                doc["localId"]
                async for doc in client.district_db["local_district"].find(
                    {"metroId": metroId}
                )
            ]
            all_indices = (
                await client.stats_db["diversity_index"]
                .find({"localId": {"$in": localIds_of_same_metroId}})
                .to_list(500)
            )
            all_indices.sort(key=lambda x: x["ageDiversityRank"])

            # ============================
            #    indexHistoryParagraph
            # ============================
            years = list(
                {doc["year"] async for doc in client.stats_db["age_hist"].find()}
            )
            years.sort()
            history_candidate = [
                await client.stats_db["age_hist"].find_one(
                    {
                        "year": year,
                        "level": 2,
                        "councilorType": "candidate",
                        "method": "equal",
                        "metroId": metroId,
                        "localId": localId,
                    }
                )
                for year in years
            ]
            history_elected = [
                await client.stats_db["age_hist"].find_one(
                    {
                        "year": year,
                        "level": 2,
                        "councilorType": "elected",
                        "method": "equal",
                        "metroId": metroId,
                        "localId": localId,
                    }
                )
                for year in years
            ]

            # ============================
            #    ageHistogramParagraph
            # ============================
            age_stat_elected = (
                await client.stats_db["age_stat"]
                .aggregate(
                    [
                        {
                            "$match": {
                                "level": 2,
                                "councilorType": "elected",
                                "metroId": metroId,
                                "localId": localId,
                            }
                        },
                        {"$sort": {"year": -1}},
                        {"$limit": 1},
                    ]
                )
                .to_list(500)
            )[0]
            most_recent_year = age_stat_elected["year"]
            age_stat_candidate = await client.stats_db["age_stat"].find_one(
                {
                    "level": 2,
                    "councilorType": "candidate",
                    "metroId": metroId,
                    "localId": localId,
                    "year": most_recent_year,
                }
            )

            divArea_id = (
                await client.stats_db["diversity_index"].find_one(
                    {"ageDiversityRank": 1}
                )
            )["localId"]
            divArea = await client.stats_db["age_stat"].find_one(
                {
                    "level": 2,
                    "councilorType": "elected",
                    "localId": divArea_id,
                    "year": most_recent_year,
                }
            )

            uniArea_id = (
                await client.stats_db["diversity_index"].find_one(
                    {"ageDiversityRank": 226}
                )
            )["localId"]
            uniArea = await client.stats_db["age_stat"].find_one(
                {
                    "level": 2,
                    "councilorType": "elected",
                    "localId": uniArea_id,
                    "year": most_recent_year,
                }
            )

            return AgeTemplateData.model_validate(
                {
                    "metroId": metroId,
                    "localId": localId,
                    "rankingParagraph": {
                        "ageDiversityIndex": age_diversity_index,
                        "allIndices": [
                            {
                                "localId": doc["localId"],
                                "rank": idx + 1,
                                "ageDiversityIndex": doc["ageDiversityIndex"],
                            }
                            for idx, doc in enumerate(all_indices)
                        ],
                    },
                    "indexHistoryParagraph": {
                        "mostRecentYear": years[-1],
                        "history": [
                            {
                                "year": year,
                                "unit": (year - 1998) / 4 + 2,
                                "candidateCount": sum(
                                    group["count"]
                                    for group in history_candidate[idx]["data"]
                                ),
                                "candidateDiversityIndex": history_candidate[idx][
                                    "diversityIndex"
                                ],
                                "candidateDiversityRank": history_candidate[idx][
                                    "diversityRank"
                                ],
                                "electedDiversityIndex": history_elected[idx][
                                    "diversityIndex"
                                ],
                                "electedDiversityRank": history_elected[idx][
                                    "diversityRank"
                                ],
                            }
                            for idx, year in enumerate(years)
                        ],
                    },
                    "ageHistogramParagraph": {
                        "year": most_recent_year,
                        "candidateCount": age_stat_candidate["data"][0]["population"],
                        "electedCount": age_stat_elected["data"][0]["population"],
                        "firstQuintile": age_stat_elected["data"][0]["firstquintile"],
                        "lastQuintile": age_stat_elected["data"][0]["lastquintile"],
                        "divArea": {
                            "localId": divArea_id,
                            "firstQuintile": divArea["data"][0]["firstquintile"],
                            "lastQuintile": divArea["data"][0]["lastquintile"],
                        },
                        "uniArea": {
                            "localId": uniArea_id,
                            "firstQuintile": uniArea["data"][0]["firstquintile"],
                            "lastQuintile": uniArea["data"][0]["lastquintile"],
                        },
                    },
                }
            )

        case FactorType.party:
            party_diversity_index = local_stat["partyDiversityIndex"]
            return PartyTemplateData.model_validate(
                {"partyDiversityIndex": party_diversity_index}
            )


T = TypeVar(
    "T",
    GenderChartDataPoint,
    AgeChartDataPoint,
    PartyChartDataPoint,
)


@router.get("/chart-data/{metroId}/{localId}")
async def getLocalChartData(
    metroId: int, localId: int, factor: FactorType
) -> ErrorResponse | ChartData[T]:
    if (
        await client.district_db["local_district"].find_one(
            {"localId": localId, "metroId": metroId}
        )
        is None
    ):
        return ErrorResponse.model_validate(
            {
                "error": "RegionCodeError",
                "code": REGION_CODE_ERR,
                "message": f"No local district with metroId {metroId} and localId {localId}.",
            }
        )

    councilors = client.council_db["local_councilor"].find({"localId": localId})

    match factor:
        case FactorType.gender:
            gender_list = [councilor["gender"] async for councilor in councilors]
            gender_count = diversity.count(gender_list)
            return ChartData[GenderChartDataPoint].model_validate(
                {
                    "data": [
                        {"gender": gender, "count": gender_count[gender]}
                        for gender in gender_count
                    ]
                }
            )

        case FactorType.age:
            age_list = [councilor["age"] async for councilor in councilors]
            age_count = diversity.count(age_list, stair=AGE_STAIR)
            return ChartData[AgeChartDataPoint].model_validate(
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

        case FactorType.party:
            party_list = [councilor["jdName"] async for councilor in councilors]
            party_count = diversity.count(party_list)
            return ChartData[PartyChartDataPoint].model_validate(
                {
                    "data": [
                        {"party": party, "count": party_count[party]}
                        for party in party_count
                    ]
                }
            )
