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

    match ageHistType:
        case AgeHistDataTypes.elected:
            collection_name = f"지선-당선_{year}_1level_{method}"
        case AgeHistDataTypes.candidate:
            collection_name = f"지선-후보_{year}_1level_{method}"

    if collection_name not in await MongoDB.client.age_hist_db.list_collection_names():
        return BasicResponse.ErrorResponse.model_validate(
            {
                "error": "CollectionNotExistError",
                "code": BasicResponse.COLLECTION_NOT_EXIST_ERR,
                "message": f"No collection with name f{collection_name}. Perhaps the year is wrong?",
            }
        )

    histogram = await MongoDB.client.age_hist_db[collection_name].find_one(
        {"metroId": metroId}
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

    match ageHistType:
        case AgeHistDataTypes.elected:
            collection_name = f"지선-당선_{year}_2level_{method}"
        case AgeHistDataTypes.candidate:
            collection_name = f"지선-후보_{year}_2level_{method}"

    if collection_name not in await MongoDB.client.age_hist_db.list_collection_names():
        return BasicResponse.ErrorResponse.model_validate(
            {
                "error": "CollectionNotExistError",
                "code": BasicResponse.COLLECTION_NOT_EXIST_ERR,
                "message": f"No collection with name f{collection_name}. Perhaps the year is wrong?",
            }
        )

    histogram = await MongoDB.client.age_hist_db[collection_name].find_one(
        {"metroId": metroId, "localId": localId}
    )

    return MetroAgeHistData.model_validate(
        {"metroId": metroId, "localId": localId, "data": histogram["data"]}
    )
