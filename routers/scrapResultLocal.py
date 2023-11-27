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
            councilors = (
                await client.council_db["local_councilor"]
                .find({"metroId": metroId, "localId": localId})
                .to_list(500)
            )
            gender_list = [councilor["gender"] for councilor in councilors]
            gender_count = diversity.count(gender_list)
            return GenderTemplateDataLocal.model_validate(
                {
                    "metroId": metroId,
                    "localId": localId,
                    "genderDiversityIndex": local_stat["genderDiversityIndex"],
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
                                # "candidateCount": 0,
                                "candidateDiversityIndex": history_candidate[idx][
                                    "diversityIndex"
                                ],
                                "candidateDiversityRank": history_candidate[idx][
                                    "diversityRank"
                                ],
                                # "candidateDiversityIndex": 0.0,
                                # "candidateDiversityRank": 0,
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
            councilors = (
                await client.council_db["local_councilor"]
                .find({"metroId": metroId, "localId": localId})
                .to_list(500)
            )
            party_list = [councilor["jdName"] for councilor in councilors]
            party_count = diversity.count(party_list)

            candidates = (
                await client.council_db["local_councilor_candidate"]
                .find({"metroId": metroId, "localId": localId})
                .to_list(500)
            )
            candidate_party_list = [candidate["jdName"] for candidate in candidates]
            candidate_party_count = diversity.count(candidate_party_list)
            return PartyTemplateDataLocal.model_validate(
                {
                    "metroId": metroId,
                    "localId": localId,
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

    councilors = (
        await client.council_db["local_councilor"]
        .find({"localId": localId})
        .to_list(5000)
    )

    if councilors is None or len(councilors) == 0:
        return NO_DATA_ERROR_RESPONSE

    match factor:
        case FactorType.gender:
            gender_list = [councilor["gender"] for councilor in councilors]
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
            age_list = [councilor["age"] for councilor in councilors]
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
            party_list = [councilor["jdName"] for councilor in councilors]
            party_count = diversity.count(party_list)
            return ChartData[PartyChartDataPoint].model_validate(
                {
                    "data": [
                        {"party": party, "count": party_count[party]}
                        for party in party_count
                    ]
                }
            )
