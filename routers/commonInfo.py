from fastapi import APIRouter
from model import MongoDB, CommonInfo

router = APIRouter(prefix="/localCouncil", tags=["localCouncil"])


@router.get("/regionInfo")
async def getRegionInfo() -> list[CommonInfo.RegionInfo]:
    regions = []
    async for metro in MongoDB.client.district_db.get_collection(
        "metro_district"
    ).find():
        local_districts = []
        async for local in MongoDB.client.district_db.get_collection(
            "local_district"
        ).find({"metro_id": metro["metro_id"]}):
            local_districts.append(CommonInfo.LocalInfo.model_validate({"name": local["name_ko"], "id": local["local_id"]}))
        regions.append(
            CommonInfo.RegionInfo.model_validate(
                {
                    "name": metro["name_ko"],
                    "id": metro["metro_id"],
                    "local": local_districts,
                }
            )
        )
    return regions


@router.get("/partyInfo")
async def getPartyInfo() -> list[CommonInfo.PartyInfo]:
    parties = []
    async for party in MongoDB.client.district_db.get_collection("party").find():
        parties.append(
            CommonInfo.PartyInfo.model_validate(
                {"name": party["name"], "color": party["color"]}
            )
        )
    return parties
