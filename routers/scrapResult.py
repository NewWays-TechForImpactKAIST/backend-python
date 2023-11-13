from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def getScrapResult():
    try:
        return {"message": "No World"}
    except Exception as e:
        print(e)
        return {"message": "Error"}