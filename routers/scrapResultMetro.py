from typing import TypeVar
from fastapi import APIRouter
from model.BasicResponse import ErrorResponse, REGION_CODE_ERR
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
    metroId: int, factor: FactorType
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
            councilors = (
                await client.council_db["metro_councilor"]
                .find({"metroId": metroId})
                .to_list(500)
            )
            gender_list = [councilor["gender"] for councilor in councilors]
            gender_count = diversity.count(gender_list)
            return GenderTemplateDataMetro.model_validate(
                {
                    "metroId": metroId,
                    "genderDiversityIndex": metro_stat["genderDiversityIndex"],
                    "current": {
                        "year": 2022,
                        "malePop": gender_count["남"],
                        "femalePop": gender_count["여"],
                    },
                    "prev": {
                        "year": 0,
                        "malePop": 0,
                        "femalePop": 0,
                    },
                    "meanMalePop": 0.0,
                    "meanFemalePop": 0.0,
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
            # age_stat_elected = (
            #     await client.stats_db["age_hist"]
            #     .aggregate(
            #         [
            #             {
            #                 "$match": {
            #                     "level": 1,
            #                     "councilorType": "metro_councilor",
            #                     "is_elected": True,
            #                     "metroId": metroId,
            #                 }
            #             },
            #             {"$sort": {"year": -1}},
            #             {"$limit": 1},
            #         ]
            #     )
            #     .to_list(500)
            # )[0]
            # most_recent_year = age_stat_elected["year"]
            # age_stat_candidate = await client.stats_db["age_hist"].find_one(
            #     {
            #         "level": 1,
            #         "councilorType": "metro_councilor",
            #         "is_elected": False,
            #         "metroId": metroId,
            #         "year": most_recent_year,
            #     }
            # )

            # divArea_id = (
            #     await client.stats_db["diversity_index"].find_one(
            #         {"metroId": {"$exists": True}, "ageDiversityRank": 1}
            #     )
            # )["metroId"]
            # divArea = await client.stats_db["age_hist"].find_one(
            #     {
            #         "level": 1,
            #         "councilorType": "metro_councilor",
            #         "is_elected": True,
            #         "metroId": divArea_id,
            #         "year": most_recent_year,
            #     }
            # )

            # uniArea_id = (
            #     await client.stats_db["diversity_index"].find_one(
            #         # {"metroId": {"$exists": True}, "ageDiversityRank": 17}
            #         {"metroId": {"$exists": True}, "ageDiversityRank": 15}
            #     )
            # )["metroId"]
            # uniArea = await client.stats_db["age_hist"].find_one(
            #     {
            #         "level": 1,
            #         "councilorType": "metro_councilor",
            #         "is_elected": True,
            #         "metroId": uniArea_id,
            #         "year": most_recent_year,
            #     }
            # )

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
                                # "electedDiversityIndex": history_elected[idx][
                                #     "diversityIndex"
                                # ],
                                # "electedDiversityRank": history_elected[idx][
                                #     "diversityRank"
                                # ],
                                "electedDiversityIndex": 0.003141592,
                                "electedDiversityRank": 99999,
                            }
                            for idx, year in enumerate(years)
                        ],
                    },
                    "ageHistogramParagraph": {
                        # "year": most_recent_year,
                        # "candidateCount": age_stat_candidate["data"][0]["population"],
                        # "electedCount": age_stat_elected["data"][0]["population"],
                        # "firstQuintile": age_stat_elected["data"][0]["firstquintile"],
                        # "lastQuintile": age_stat_elected["data"][0]["lastquintile"],
                        # "divArea": {
                        #     "metroId": divArea_id,
                        #     "firstQuintile": divArea["data"][0]["firstquintile"],
                        #     "lastQuintile": divArea["data"][0]["lastquintile"],
                        # },
                        # "uniArea": {
                        #     "metroId": uniArea_id,
                        #     "firstQuintile": uniArea["data"][0]["firstquintile"],
                        #     "lastQuintile": uniArea["data"][0]["lastquintile"],
                        # },
                        "year": 2022,
                        "candidateCount": 99999,
                        "electedCount": 88888,
                        "firstQuintile": 74,
                        "lastQuintile": 21,
                        "divArea": {
                            "metroId": 1,
                            "firstQuintile": 45,
                            "lastQuintile": 20,
                        },
                        "uniArea": {
                            "metroId": 8,
                            "firstQuintile": 86,
                            "lastQuintile": 43,
                        },
                    },
                }
            )

        case FactorType.party:
            party_diversity_index = metro_stat["partyDiversityIndex"]
            councilors = (
                await client.council_db["metro_councilor"]
                .find({"metroId": metroId})
                .to_list(500)
            )
            party_list = [councilor["jdName"] for councilor in councilors]
            party_count = diversity.count(party_list)

            candidates = (
                await client.council_db["metro_councilor_candidate"]
                .find({"metroId": metroId})
                .to_list(500)
            )
            candidate_party_list = [candidate["jdName"] for candidate in candidates]
            candidate_party_count = diversity.count(candidate_party_list)
            return PartyTemplateDataMetro.model_validate(
                {
                    "metroId": metroId,
                    "partyDiversityIndex": party_diversity_index,
                    "prevElected": [
                        {"party": "포도당", "count": 6},
                        {"party": "유당", "count": 6},
                        {"party": "과당", "count": 5},
                    ],
                    "currentElected": [
                        {"party": party, "count": party_count[party]}
                        for party in party_count
                    ],
                    "currentCandidate": [
                        {"party": party, "count": candidate_party_count[party]}
                        for party in candidate_party_count
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
async def getLocalChartData(
    metroId: int, factor: FactorType
) -> ErrorResponse | ChartData[T]:
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

    councilors = client.council_db["metro_councilor"].find({"metroId": metroId})

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
