from fastapi import APIRouter
from model import BasicResponse, MongoDB
from model.AgeHist import (
    AgeHistDataTypes,
    AgeHistMethodTypes,
    MetroAgeHistData,
    NationalAgeHistData,
)


router = APIRouter(prefix="/age-hist", tags=["age-hist"])


@router.get("/")
async def getNationalAgeHistData(
    ageHistType: AgeHistDataTypes, year: int, method: AgeHistMethodTypes
) -> BasicResponse.ErrorResponse | NationalAgeHistData:
    # histogram = await MongoDB.client.stats_db["age_hist"].find_one(
    #     {
    #         "councilorType": "national_councilor",
    #         "is_elected": ageHistType == AgeHistDataTypes.elected,
    #         "year": year,
    #         "method": method,
    #     }
    # )

    # if histogram is None:
    #     return BasicResponse.ErrorResponse.model_validate(
    #         {
    #             "error": "NoDataError",
    #             "code": BasicResponse.NO_DATA_ERROR,
    #             "message": "No data retrieved with the provided input.",
    #         }
    #     )

    # return NationalAgeHistData.model_validate({"data": histogram["data"]})
    return NationalAgeHistData.model_validate(
        {
            "data": [
                {
                    "minAge": 21,
                    "maxAge": 22,
                    "count": 75,
                    "ageGroup": 0,
                },
                {
                    "minAge": 22,
                    "maxAge": 23,
                    "count": 87,
                    "ageGroup": 1,
                },
                {
                    "minAge": 29,
                    "maxAge": 30,
                    "count": 104,
                    "ageGroup": 2,
                },
                {
                    "minAge": 45,
                    "maxAge": 46,
                    "count": 354,
                    "ageGroup": 2,
                },
                {
                    "minAge": 46,
                    "maxAge": 47,
                    "count": 463,
                    "ageGroup": 3,
                },
                {
                    "minAge": 63,
                    "maxAge": 64,
                    "count": 240,
                    "ageGroup": 4,
                },
            ]
        }
    )


@router.get("/{metroId}")
async def getMetroAgeHistData(
    metroId: int, ageHistType: AgeHistDataTypes, year: int, method: AgeHistMethodTypes
) -> BasicResponse.ErrorResponse | MetroAgeHistData:
    # if (
    #     await MongoDB.client.district_db["metro_district"].find_one(
    #         {"metroId": metroId}
    #     )
    #     is None
    # ):
    #     return BasicResponse.ErrorResponse.model_validate(
    #         {
    #             "error": "RegionCodeError",
    #             "code": BasicResponse.REGION_CODE_ERR,
    #             "message": f"No metro district with metroId {metroId}.",
    #         }
    #     )

    # histogram = await MongoDB.client.stats_db["age_hist"].find_one(
    #     {
    #         "level": 1,
    #         "councilorType": "metro_councilor",
    #         "is_elected": ageHistType == AgeHistDataTypes.elected,
    #         "year": year,
    #         "method": method,
    #         "metroId": metroId,
    #     }
    # )

    # if histogram is None:
    #     return BasicResponse.ErrorResponse.model_validate(
    #         {
    #             "error": "NoDataError",
    #             "code": BasicResponse.NO_DATA_ERROR,
    #             "message": "No data retrieved with the provided input.",
    #         }
    #     )

    # return MetroAgeHistData.model_validate(
    #     {"metroId": metroId, "data": histogram["data"]}
    # )
    return MetroAgeHistData.model_validate(
        {
            "metroId": metroId,
            "data": [
                {
                    "minAge": 21,
                    "maxAge": 22,
                    "count": 75,
                    "ageGroup": 0,
                },
                {
                    "minAge": 22,
                    "maxAge": 23,
                    "count": 87,
                    "ageGroup": 1,
                },
                {
                    "minAge": 29,
                    "maxAge": 30,
                    "count": 104,
                    "ageGroup": 2,
                },
                {
                    "minAge": 45,
                    "maxAge": 46,
                    "count": 354,
                    "ageGroup": 2,
                },
                {
                    "minAge": 46,
                    "maxAge": 47,
                    "count": 463,
                    "ageGroup": 3,
                },
                {
                    "minAge": 63,
                    "maxAge": 64,
                    "count": 240,
                    "ageGroup": 4,
                },
            ],
        }
    )


@router.get("/{metroId}/{localId}")
async def getLocalAgeHistData(
    metroId: int,
    localId: int,
    ageHistType: AgeHistDataTypes,
    year: int,
    method: AgeHistMethodTypes,
) -> BasicResponse.ErrorResponse | MetroAgeHistData:
    if (
        await MongoDB.client.district_db["local_district"].find_one(
            {"metroId": metroId, "localId": localId}
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

    histogram = await MongoDB.client.stats_db["age_hist"].find_one(
        {
            "level": 2,
            "councilorType": "local_councilor",
            "is_elected": ageHistType == AgeHistDataTypes.elected,
            "year": year,
            "method": method,
            "metroId": metroId,
            "localId": localId,
        }
    )

    if histogram is None:
        return BasicResponse.ErrorResponse.model_validate(
            {
                "error": "NoDataError",
                "code": BasicResponse.NO_DATA_ERROR,
                "message": "No data retrieved with the provided input.",
            }
        )

    return MetroAgeHistData.model_validate(
        {"metroId": metroId, "localId": localId, "data": histogram["data"]}
    )
