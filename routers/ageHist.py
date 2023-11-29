from fastapi import APIRouter
from model import BasicResponse, MongoDB
from model.AgeHist import (
    AgeHistDataTypes,
    AgeHistMethodTypes,
    LocalAgeHistData,
    MetroAgeHistData,
    NationalAgeHistData,
)


router = APIRouter(prefix="/age-hist", tags=["age-hist"])


@router.get("/")
async def getNationalAgeHistData(
    ageHistType: AgeHistDataTypes, year: int, method: AgeHistMethodTypes
) -> BasicResponse.ErrorResponse | NationalAgeHistData:
    histogram = await MongoDB.client.stats_db["age_hist"].find_one(
        {
            "councilorType": "national_councilor",
            "is_elected": ageHistType == AgeHistDataTypes.elected,
            "year": year,
            "method": method,
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

    return NationalAgeHistData.model_validate({"data": histogram["data"]})


@router.get("/{metroId}")
async def getMetroAgeHistData(
    metroId: int, ageHistType: AgeHistDataTypes, year: int, method: AgeHistMethodTypes
) -> BasicResponse.ErrorResponse | MetroAgeHistData:
    if (
        await MongoDB.client.district_db["metro_district"].find_one(
            {"metroId": metroId}
        )
        is None
    ):
        return BasicResponse.ErrorResponse.model_validate(
            {
                "error": "RegionCodeError",
                "code": BasicResponse.REGION_CODE_ERR,
                "message": f"No metro district with metroId {metroId}.",
            }
        )

    histogram = await MongoDB.client.stats_db["age_hist"].find_one(
        {
            "level": 1,
            "councilorType": "metro_councilor",
            "is_elected": ageHistType == AgeHistDataTypes.elected,
            "year": year,
            "method": method,
            "metroId": metroId,
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
        {"metroId": metroId, "data": histogram["data"]}
    )


@router.get("/{metroId}/{localId}")
async def getLocalAgeHistData(
    metroId: int,
    localId: int,
    ageHistType: AgeHistDataTypes,
    year: int,
    method: AgeHistMethodTypes,
) -> BasicResponse.ErrorResponse | LocalAgeHistData:
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

    return LocalAgeHistData.model_validate(
        {"metroId": metroId, "localId": localId, "data": histogram["data"]}
    )
