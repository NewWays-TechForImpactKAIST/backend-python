from fastapi import APIRouter

from model.ResponseType import *

router = APIRouter(prefix="/localCouncil", tags=["localCouncil"])

@router.get("/regionInfo", response_model=RegionInfo)
async def getRegionInfo():
    try:
        return []
    except Exception as e:
        print(e)
        return []

@router.get("/partyInfo", response_model=PartyInfo)
async def getPartyInfo():
    try:
        return []
    except Exception as e:
        print(e)
        return []

@router.get("/template-data/{metroId}/{localId}/{factor}", response_model=Diversity)
async def getTemplateData(metroId: int, localId: int, factor: str):
    try:
        return []
    except Exception as e:
        print(e)
        return []

@router.get("/chart-data/{metroId}/{localId}/{factor}", response_model=ChartResponse)
async def getTemplateData(metroId: int, localId: int, factor: str):
    try:
        return []
    except Exception as e:
        print(e)
        return []