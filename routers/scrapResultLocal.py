from typing import TypeVar
from fastapi import APIRouter
from model.BasicResponse import ErrorResponse, REGION_CODE_ERR, NO_DATA_ERROR_RESPONSE
from model.MongoDB import client
from model.ScrapResultCommon import (
    GenderChartDataPoint,
    AgeChartDataPoint,
    PartyChartDataPoint,
    FactorType,
    ChartData,
)
from model.ScrapResultLocal import (
    GenderTemplateDataLocal,
    AgeTemplateDataLocal,
    PartyTemplateDataLocal,
)
from utils import diversity


router = APIRouter(prefix="/localCouncil", tags=["localCouncil"])

AGE_STAIR = 10


@router.get("/template-data/{metroId}/{localId}")
async def getLocalTemplateData(
    metroId: int, localId: int, factor: FactorType
) -> ErrorResponse | GenderTemplateDataLocal | AgeTemplateDataLocal | PartyTemplateDataLocal:
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

    if local_stat is None:
        return NO_DATA_ERROR_RESPONSE

    match factor:
        case FactorType.gender:
            years = list(
                {
                    doc["year"]
                    async for doc in client.stats_db["gender_hist"].find(
                        {
                            "councilorType": "local_councilor",
                            "level": 2,
                            "is_elected": True,
                            "localId": localId,
                            "metroId": metroId,
                        }
                    )
                }
            )
            years.sort()
            assert len(years) >= 2

            current = await client.stats_db["gender_hist"].find_one(
                {
                    "councilorType": "local_councilor",
                    "level": 2,
                    "is_elected": True,
                    "localId": localId,
                    "metroId": metroId,
                    "year": years[-1],
                }
            )

            previous = await client.stats_db["gender_hist"].find_one(
                {
                    "councilorType": "local_councilor",
                    "level": 2,
                    "is_elected": True,
                    "localId": localId,
                    "metroId": metroId,
                    "year": years[-2],
                }
            )

            current_all = (
                await client.stats_db["gender_hist"]
                .aggregate(
                    [
                        {
                            "$match": {
                                "councilorType": "local_councilor",
                                "level": 2,
                                "is_elected": True,
                                "year": years[-1],
                            }
                        },
                        {
                            "$group": {
                                "_id": None,
                                "male_tot": {"$sum": "$남"},
                                "female_tot": {"$sum": "$여"},
                                "district_cnt": {"$sum": 1},
                            }
                        },
                    ]
                )
                .to_list(500)
            )
            assert len(current_all) == 1
            current_all = current_all[0]

            return GenderTemplateDataLocal.model_validate(
                {
                    "metroId": metroId,
                    "localId": localId,
                    "genderDiversityIndex": local_stat["genderDiversityIndex"],
                    "current": {
                        "year": years[-1],
                        "malePop": current["남"],
                        "femalePop": current["여"],
                    },
                    "prev": {
                        "year": years[-2],
                        "malePop": previous["남"],
                        "femalePop": previous["여"],
                    },
                    "meanMalePop": current_all["male_tot"]
                    / current_all["district_cnt"],
                    "meanFemalePop": current_all["female_tot"]
                    / current_all["district_cnt"],
                }
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
                {
                    doc["year"]
                    async for doc in client.stats_db["age_hist"].find(
                        {"councilorType": "local_councilor"}
                    )
                }
            )
            years.sort()
            history_candidate = [
                await client.stats_db["age_hist"].find_one(
                    {
                        "year": year,
                        "level": 2,
                        "councilorType": "local_councilor",
                        "is_elected": False,
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
                        "councilorType": "local_councilor",
                        "is_elected": True,
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
                                "councilorType": "local_councilor",
                                "is_elected": True,
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
                    "councilorType": "local_councilor",
                    "is_elected": False,
                    "metroId": metroId,
                    "localId": localId,
                    "year": most_recent_year,
                }
            )

            divArea_id = (
                await client.stats_db["diversity_index"].find_one(
                    {"localId": {"$exists": True}, "ageDiversityRank": 1}
                )
            )["localId"]
            divArea = await client.stats_db["age_stat"].find_one(
                {
                    "level": 2,
                    "councilorType": "local_councilor",
                    "is_elected": True,
                    "localId": divArea_id,
                    "year": most_recent_year,
                }
            )

            uniArea_id = (
                await client.stats_db["diversity_index"].find_one(
                    {"localId": {"$exists": True}, "ageDiversityRank": 226}
                )
            )["localId"]
            uniArea = await client.stats_db["age_stat"].find_one(
                {
                    "level": 2,
                    "councilorType": "local_councilor",
                    "is_elected": True,
                    "localId": uniArea_id,
                    "year": most_recent_year,
                }
            )

            return AgeTemplateDataLocal.model_validate(
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
            years = list(
                {
                    doc["year"]
                    async for doc in client.stats_db["party_hist"].find(
                        {
                            "councilorType": "local_councilor",
                            "level": 2,
                            "is_elected": True,
                            "localId": localId,
                            "metroId": metroId,
                        }
                    )
                }
            )
            years.sort()
            assert len(years) >= 2

            current_elected = client.stats_db["party_hist"].find(
                {
                    "councilorType": "local_councilor",
                    "level": 2,
                    "is_elected": True,
                    "localId": localId,
                    "metroId": metroId,
                    "year": years[-1],
                },
                {
                    "_id": 0,
                    "councilorType": 0,
                    "level": 0,
                    "is_elected": 0,
                    "localId": 0,
                    "metroId": 0,
                    "year": 0,
                },
            )
            current_candidate = client.stats_db["party_hist"].find(
                {
                    "councilorType": "local_councilor",
                    "level": 2,
                    "is_elected": False,
                    "localId": localId,
                    "metroId": metroId,
                    "year": years[-1],
                },
                {
                    "_id": 0,
                    "councilorType": 0,
                    "level": 0,
                    "is_elected": 0,
                    "localId": 0,
                    "metroId": 0,
                    "year": 0,
                },
            )
            previous = client.stats_db["party_hist"].find(
                {
                    "councilorType": "local_councilor",
                    "level": 2,
                    "is_elected": True,
                    "localId": localId,
                    "metroId": metroId,
                    "year": years[-2],
                },
                {
                    "_id": 0,
                    "councilorType": 0,
                    "level": 0,
                    "is_elected": 0,
                    "localId": 0,
                    "metroId": 0,
                    "year": 0,
                },
            )

            return PartyTemplateDataLocal.model_validate(
                {
                    "metroId": metroId,
                    "localId": localId,
                    "partyDiversityIndex": party_diversity_index,
                    "prevElected": [
                        {"party": party, "count": doc[party]}
                        async for doc in previous
                        for party in doc
                    ],
                    "currentElected": [
                        {"party": party, "count": doc[party]}
                        async for doc in current_elected
                        for party in doc
                    ],
                    "currentCandidate": [
                        {"party": party, "count": doc[party]}
                        async for doc in current_candidate
                        for party in doc
                    ],
                }
            )


@router.get("/chart-data/{metroId}/{localId}")
async def getLocalChartData(
    metroId: int, localId: int, factor: FactorType
) -> ErrorResponse | ChartData[GenderChartDataPoint] | ChartData[
    AgeChartDataPoint
] | ChartData[PartyChartDataPoint]:
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

    match factor:
        case FactorType.gender:
            gender_cnt = (
                await client.stats_db["gender_hist"]
                .find(
                    {
                        "councilorType": "local_councilor",
                        "level": 2,
                        "is_elected": True,
                        "localId": localId,
                        "metroId": metroId,
                    }
                )
                .sort({"year": -1})
                .limit(1)
                .to_list(5)
            )[0]

            return ChartData[GenderChartDataPoint].model_validate(
                {
                    "data": [
                        {"gender": "남", "count": gender_cnt["남"]},
                        {"gender": "여", "count": gender_cnt["여"]},
                    ]
                }
            )

        case FactorType.age:
            age_cnt = (
                await client.stats_db["age_hist"]
                .find(
                    {
                        "councilorType": "local_councilor",
                        "level": 2,
                        "is_elected": True,
                        "method": "equal",
                        "localId": localId,
                        "metroId": metroId,
                    }
                )
                .sort({"year": -1})
                .limit(1)
                .to_list(5)
            )[0]
            age_list = [
                age["minAge"] for age in age_cnt["data"] for _ in range(age["count"])
            ]
            age_stair = diversity.count(age_list, stair=AGE_STAIR)
            return ChartData[AgeChartDataPoint].model_validate(
                {
                    "data": [
                        {
                            "minAge": age,
                            "maxAge": age + AGE_STAIR,
                            "count": age_stair[age],
                        }
                        for age in age_stair
                    ]
                }
            )

        case FactorType.party:
            party_count = (
                await client.stats_db["party_hist"]
                .find(
                    {
                        "councilorType": "local_councilor",
                        "level": 2,
                        "is_elected": True,
                        "localId": localId,
                        "metroId": metroId,
                    }
                )
                .sort({"year": -1})
                .limit(1)
                .to_list(5)
            )[0]
            return ChartData[PartyChartDataPoint].model_validate(
                {
                    "data": [
                        {"party": party, "count": party_count[party]}
                        for party in party_count
                        if party
                        not in [
                            "_id",
                            "councilorType",
                            "level",
                            "is_elected",
                            "localId",
                            "metroId",
                            "year",
                        ]
                    ]
                }
            )
