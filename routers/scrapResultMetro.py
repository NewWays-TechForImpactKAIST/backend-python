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
from model.ScrapResultMetro import (
    GenderTemplateDataMetro,
    AgeTemplateDataMetro,
    PartyTemplateDataMetro,
)
from utils import diversity


router = APIRouter(prefix="/metroCouncil", tags=["metroCouncil"])

AGE_STAIR = 10


@router.get("/template-data/{metroId}")
async def getMetroTemplateData(
    metroId: int, factor: FactorType, year: int = 2022
) -> ErrorResponse | GenderTemplateDataMetro | AgeTemplateDataMetro | PartyTemplateDataMetro:
    if (
        await client.district_db["metro_district"].find_one({"metroId": metroId})
        is None
    ):
        return ErrorResponse.model_validate(
            {
                "error": "RegionCodeError",
                "code": REGION_CODE_ERR,
                "message": f"No metro district with metroId {metroId}.",
            }
        )

    metro_stat = await client.stats_db["diversity_index"].find_one({"metroId": metroId})

    match factor:
        case FactorType.gender:
            years = list(
                {
                    doc["year"]
                    async for doc in client.stats_db["gender_hist"].find(
                        {
                            "councilorType": "metro_councilor",
                            "level": 1,
                            "is_elected": True,
                            "metroId": metroId,
                        }
                    )
                }
            )
            years.sort()
            assert len(years) >= 2
            year_index = years.index(year)
            if year_index == 0:
                return NO_DATA_ERROR_RESPONSE

            current = await client.stats_db["gender_hist"].find_one(
                {
                    "councilorType": "metro_councilor",
                    "level": 1,
                    "is_elected": True,
                    "metroId": metroId,
                    "year": years[year_index],
                }
            )

            current_candidate = await client.stats_db["gender_hist"].find_one(
                {
                    "councilorType": "metro_councilor",
                    "level": 1,
                    "is_elected": False,
                    "metroId": metroId,
                    "year": years[year_index],
                }
            )

            previous = await client.stats_db["gender_hist"].find_one(
                {
                    "councilorType": "metro_councilor",
                    "level": 1,
                    "is_elected": True,
                    "metroId": metroId,
                    "year": years[year_index - 1],
                }
            )

            previous_candidate = await client.stats_db["gender_hist"].find_one(
                {
                    "councilorType": "metro_councilor",
                    "level": 1,
                    "is_elected": False,
                    "metroId": metroId,
                    "year": years[year_index],
                }
            )

            current_all = (
                await client.stats_db["gender_hist"]
                .aggregate(
                    [
                        {
                            "$match": {
                                "councilorType": "metro_councilor",
                                "level": 1,
                                "is_elected": True,
                                "year": years[year_index],
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

            return GenderTemplateDataMetro.model_validate(
                {
                    "metroId": metroId,
                    "genderDiversityIndex": metro_stat["genderDiversityIndex"],
                    "current": {
                        "year": years[year_index],
                        "malePop": current["남"],
                        "femalePop": current["여"],
                    },
                    "currentCandidate": {
                        "year": years[year_index],
                        "malePop": current_candidate["남"],
                        "femalePop": current_candidate["여"],
                    },
                    "prev": {
                        "year": years[year_index - 1],
                        "malePop": previous["남"],
                        "femalePop": previous["여"],
                    },
                    "prevCandidate": {
                        "year": years[year_index],
                        "malePop": previous_candidate["남"],
                        "femalePop": previous_candidate["여"],
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
            age_diversity_index = metro_stat["ageDiversityIndex"]

            all_metroIds = [
                doc["metroId"]
                async for doc in client.district_db["metro_district"].find()
            ]
            all_indices = (
                await client.stats_db["diversity_index"]
                .find({"metroId": {"$in": all_metroIds}})
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
                        {"councilorType": "metro_councilor"}
                    )
                }
            )
            years.sort()
            year_index = years.index(year)
            if year_index == 0:
                return NO_DATA_ERROR_RESPONSE

            history_candidate = [
                await client.stats_db["age_hist"].find_one(
                    {
                        "year": year,
                        "level": 1,
                        "councilorType": "metro_councilor",
                        "is_elected": False,
                        "method": "equal",
                        "metroId": metroId,
                    }
                )
                for year in years
            ]
            history_elected = [
                await client.stats_db["age_hist"].find_one(
                    {
                        "year": year,
                        "level": 1,
                        "councilorType": "metro_councilor",
                        "is_elected": True,
                        "method": "equal",
                        "metroId": metroId,
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
                                "level": 1,
                                "councilorType": "metro_councilor",
                                "is_elected": True,
                                "metroId": metroId,
                                "year": years[year_index],
                            }
                        },
                    ]
                )
                .to_list(500)
            )[0]
            most_recent_year = year
            age_stat_candidate = await client.stats_db["age_stat"].find_one(
                {
                    "level": 1,
                    "councilorType": "metro_councilor",
                    "is_elected": False,
                    "metroId": metroId,
                    "year": most_recent_year,
                }
            )

            divArea_id = (
                await client.stats_db["diversity_index"].find_one(
                    {"metroId": {"$exists": True}, "ageDiversityRank": 1}
                )
            )["metroId"]
            divArea = await client.stats_db["age_stat"].find_one(
                {
                    "level": 1,
                    "councilorType": "metro_councilor",
                    "is_elected": True,
                    "metroId": divArea_id,
                    "year": most_recent_year,
                }
            )

            uniArea_id = (
                await client.stats_db["diversity_index"].find_one(
                    {"metroId": {"$exists": True}, "ageDiversityRank": 16}
                )
            )["metroId"]
            uniArea = await client.stats_db["age_stat"].find_one(
                {
                    "level": 1,
                    "councilorType": "metro_councilor",
                    "is_elected": True,
                    "metroId": uniArea_id,
                    "year": most_recent_year,
                }
            )

            return AgeTemplateDataMetro.model_validate(
                {
                    "metroId": metroId,
                    "rankingParagraph": {
                        "ageDiversityIndex": age_diversity_index,
                        "allIndices": [
                            {
                                "metroId": doc["metroId"],
                                "rank": doc["ageDiversityRank"],
                                "ageDiversityIndex": doc["ageDiversityIndex"],
                            }
                            for doc in all_indices
                        ],
                    },
                    "indexHistoryParagraph": {
                        "mostRecentYear": years[year_index],
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
                            "metroId": divArea_id,
                            "firstQuintile": divArea["data"][0]["firstquintile"],
                            "lastQuintile": divArea["data"][0]["lastquintile"],
                        },
                        "uniArea": {
                            "metroId": uniArea_id,
                            "firstQuintile": uniArea["data"][0]["firstquintile"],
                            "lastQuintile": uniArea["data"][0]["lastquintile"],
                        },
                    },
                }
            )

        case FactorType.party:
            party_diversity_index = metro_stat["partyDiversityIndex"]
            years = list(
                {
                    doc["year"]
                    async for doc in client.stats_db["party_hist"].find(
                        {
                            "councilorType": "metro_councilor",
                            "level": 1,
                            "is_elected": True,
                            "metroId": metroId,
                        }
                    )
                }
            )
            years.sort()
            assert len(years) >= 2

            year_index = years.index(year)
            if year_index == 0:
                return NO_DATA_ERROR_RESPONSE

            current_elected = client.stats_db["party_hist"].find(
                {
                    "councilorType": "metro_councilor",
                    "level": 1,
                    "is_elected": True,
                    "metroId": metroId,
                    "year": years[year_index],
                },
                {
                    "_id": 0,
                    "councilorType": 0,
                    "level": 0,
                    "is_elected": 0,
                    "metroId": 0,
                    "year": 0,
                },
            )
            current_candidate = client.stats_db["party_hist"].find(
                {
                    "councilorType": "metro_councilor",
                    "level": 1,
                    "is_elected": False,
                    "metroId": metroId,
                    "year": years[year_index],
                },
                {
                    "_id": 0,
                    "councilorType": 0,
                    "level": 0,
                    "is_elected": 0,
                    "metroId": 0,
                    "year": 0,
                },
            )
            previous = client.stats_db["party_hist"].find(
                {
                    "councilorType": "metro_councilor",
                    "level": 1,
                    "is_elected": True,
                    "metroId": metroId,
                    "year": years[year_index - 1],
                },
                {
                    "_id": 0,
                    "councilorType": 0,
                    "level": 0,
                    "is_elected": 0,
                    "metroId": 0,
                    "year": 0,
                },
            )

            return PartyTemplateDataMetro.model_validate(
                {
                    "metroId": metroId,
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


T = TypeVar(
    "T",
    GenderChartDataPoint,
    AgeChartDataPoint,
    PartyChartDataPoint,
)


@router.get("/chart-data/{metroId}")
async def getMetroChartData(
    metroId: int, factor: FactorType, year: int = 2022
) -> ErrorResponse | ChartData[GenderChartDataPoint] | ChartData[
    AgeChartDataPoint
] | ChartData[PartyChartDataPoint]:
    if (
        await client.district_db["metro_district"].find_one({"metroId": metroId})
        is None
    ):
        return ErrorResponse.model_validate(
            {
                "error": "RegionCodeError",
                "code": REGION_CODE_ERR,
                "message": f"No metro district with metroId {metroId}.",
            }
        )

    match factor:
        case FactorType.gender:
            gender_cnt = (
                await client.stats_db["gender_hist"]
                .find(
                    {
                        "councilorType": "metro_councilor",
                        "level": 1,
                        "is_elected": True,
                        "metroId": metroId,
                        "year": year,
                    }
                )
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
                        "councilorType": "metro_councilor",
                        "level": 1,
                        "is_elected": True,
                        "method": "equal",
                        "metroId": metroId,
                        "year": year,
                    }
                )
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
                        "councilorType": "metro_councilor",
                        "level": 1,
                        "is_elected": True,
                        "metroId": metroId,
                        "year": year,
                    }
                )
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
                            "metroId",
                            "year",
                        ]
                    ]
                }
            )
