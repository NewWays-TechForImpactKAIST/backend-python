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
    factor: FactorType,
) -> ErrorResponse | GenderTemplateDataNational | AgeTemplateDataNational | PartyTemplateDataNational:
    national_stat = await client.stats_db["diversity_index"].find_one(
        {"national": True}
    )

    match factor:
        case FactorType.gender:
            return GenderTemplateDataNational.model_validate(
                {"genderDiversityIndex": national_stat["genderDiversityIndex"]}
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
                                "level": 2,
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
                    },
                }
            )

        case FactorType.party:
            party_diversity_index = national_stat["partyDiversityIndex"]
            return PartyTemplateDataNational.model_validate(
                {"partyDiversityIndex": party_diversity_index}
            )


T = TypeVar(
    "T",
    GenderChartDataPoint,
    AgeChartDataPoint,
    PartyChartDataPoint,
)


@router.get("/chart-data")
async def getNationalChartData(factor: FactorType) -> ErrorResponse | ChartData[T]:
    councilors = client.council_db["national_councilor"].find()

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
