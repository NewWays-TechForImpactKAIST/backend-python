from fastapi import APIRouter
from model import BasicResponse, MongoDB
from model.AgeHist import AgeHistDataTypes, AgeHistMethodTypes, MetroAgeHistData


router = APIRouter(prefix="/localCouncil", tags=["localCouncil"])


@router.get("/age-hist/{metroId}")
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
            "councilorType": (
                "elected" if ageHistType == AgeHistDataTypes.elected else "candidate"
            ),
            "year": year,
            "method": method,
            "metroId": metroId,
        }
    )

    return MetroAgeHistData.model_validate(
        {"metroId": metroId, "data": histogram["data"]}
    )


@router.get("/age-hist/{metroId}/{localId}")
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
            "councilorType": (
                "elected" if ageHistType == AgeHistDataTypes.elected else "candidate"
            ),
            "year": year,
            "method": method,
            "metroId": metroId,
            "localId": localId,
        }
    )

    return MetroAgeHistData.model_validate(
        {"metroId": metroId, "localId": localId, "data": histogram["data"]}
    )
