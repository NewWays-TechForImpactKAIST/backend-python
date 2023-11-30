from typing import TypeVar
from fastapi import APIRouter
from model.BasicResponse import ErrorResponse, NO_DATA_ERROR_RESPONSE
from model.MongoDB import client
from model.ScrapResultCommon import (
    GenderChartDataPoint,
    AgeChartDataPoint,
    PartyChartDataPoint,
    FactorType,
    ChartData,
)
from model.ScrapResultNational import (
    GenderTemplateDataNational,
    AgeTemplateDataNational,
    PartyTemplateDataNational,
)
from utils import diversity


router = APIRouter(prefix="/nationalCouncil", tags=["nationalCouncil"])

AGE_STAIR = 10


@router.get("/template-data")
async def getNationalTemplateData(
    factor: FactorType, year: int = 2020
) -> ErrorResponse | GenderTemplateDataNational | AgeTemplateDataNational | PartyTemplateDataNational:
    national_stat = await client.stats_db["diversity_index"].find_one(
        {"national": True}
    )
    if national_stat is None:
        return NO_DATA_ERROR_RESPONSE

    match factor:
        case FactorType.gender:
            years = list(
                {
                    doc["year"]
                    async for doc in client.stats_db["gender_hist"].find(
                        {
                            "councilorType": "national_councilor",
                            "level": 0,
                            "is_elected": True,
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
                    "councilorType": "national_councilor",
                    "level": 0,
                    "is_elected": True,
                    "year": years[year_index],
                }
            )

            current_candidate = await client.stats_db["gender_hist"].find_one(
                {
                    "councilorType": "national_councilor",
                    "level": 0,
                    "is_elected": False,
                    "year": years[year_index - 1],
                }
            )

            previous = await client.stats_db["gender_hist"].find_one(
                {
                    "councilorType": "national_councilor",
                    "level": 0,
                    "is_elected": True,
                    "year": years[year_index],
                }
            )

            previous_candidate = await client.stats_db["gender_hist"].find_one(
                {
                    "councilorType": "national_councilor",
                    "level": 0,
                    "is_elected": False,
                    "year": years[year_index - 1],
                }
            )

            return GenderTemplateDataNational.model_validate(
                {
                    "genderDiversityIndex": national_stat["genderDiversityIndex"],
                    "current": {
                        "year": years[year_index],
                        "malePop": current["남"],
                        "femalePop": current["여"],
                    },
                    "currentCandidate": {
                        "year": years[year_index - 1],
                        "malePop": current_candidate["남"],
                        "femalePop": current_candidate["여"],
                    },
                    "prev": {
                        "year": years[year_index],
                        "malePop": previous["남"],
                        "femalePop": previous["여"],
                    },
                    "prevCandidate": {
                        "year": years[year_index - 1],
                        "malePop": previous_candidate["남"],
                        "femalePop": previous_candidate["여"],
                    },
                }
            )

        case FactorType.age:
            # ============================
            #      rankingParagraph
            # ============================
            age_diversity_index = national_stat["ageDiversityIndex"]

            # ============================
            #    indexHistoryParagraph
            # ============================
            years = list(
                {
                    doc["year"]
                    async for doc in client.stats_db["age_hist"].find(
                        {"councilorType": "national_councilor"}
                    )
                }
            )
            years.sort()
            history_candidate = [
                await client.stats_db["age_hist"].find_one(
                    {
                        "year": year,
                        "councilorType": "national_councilor",
                        "is_elected": False,
                        "method": "equal",
                    }
                )
                for year in years
            ]
            history_elected = [
                await client.stats_db["age_hist"].find_one(
                    {
                        "year": year,
                        "councilorType": "national_councilor",
                        "is_elected": True,
                        "method": "equal",
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
                                "level": 0,
                                "councilorType": "national_councilor",
                                "is_elected": True,
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
                    "councilorType": "national_councilor",
                    "is_elected": False,
                    "year": most_recent_year,
                }
            )

            return AgeTemplateDataNational.model_validate(
                {
                    "rankingParagraph": {
                        "ageDiversityIndex": age_diversity_index,
                    },
                    "indexHistoryParagraph": {
                        "mostRecentYear": years[-1],
                        "history": [
                            {
                                "year": year,
                                "unit": (year - 2000) / 4 + 2,
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
                    },
                }
            )

        case FactorType.party:
            party_diversity_index = national_stat["partyDiversityIndex"]
            years = list(
                {
                    doc["year"]
                    async for doc in client.stats_db["party_hist"].find(
                        {
                            "councilorType": "national_councilor",
                            "level": 0,
                            "is_elected": True,
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
                    "councilorType": "national_councilor",
                    "level": 0,
                    "is_elected": True,
                    "year": years[year_index],
                },
                {
                    "_id": 0,
                    "councilorType": 0,
                    "level": 0,
                    "is_elected": 0,
                    "year": 0,
                },
            )
            current_candidate = client.stats_db["party_hist"].find(
                {
                    "councilorType": "national_councilor",
                    "level": 0,
                    "is_elected": False,
                    "year": years[year_index],
                },
                {
                    "_id": 0,
                    "councilorType": 0,
                    "level": 0,
                    "is_elected": 0,
                    "year": 0,
                },
            )
            previous = client.stats_db["party_hist"].find(
                {
                    "councilorType": "national_councilor",
                    "level": 0,
                    "is_elected": True,
                    "year": years[year_index - 1],
                },
                {
                    "_id": 0,
                    "councilorType": 0,
                    "level": 0,
                    "is_elected": 0,
                    "year": 0,
                },
            )

            return PartyTemplateDataNational.model_validate(
                {
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


@router.get("/chart-data")
async def getNationalChartData(
    factor: FactorType,
) -> ErrorResponse | ChartData[GenderChartDataPoint] | ChartData[
    AgeChartDataPoint
] | ChartData[PartyChartDataPoint]:
    match factor:
        case FactorType.gender:
            gender_cnt = (
                await client.stats_db["gender_hist"]
                .find(
                    {
                        "councilorType": "national_councilor",
                        "level": 0,
                        "is_elected": True,
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
                        "councilorType": "national_councilor",
                        "level": 0,
                        "is_elected": True,
                        "method": "equal",
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
                        "councilorType": "national_councilor",
                        "level": 0,
                        "is_elected": True,
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
                            "year",
                        ]
                    ]
                }
            )
