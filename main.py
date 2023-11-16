from fastapi import FastAPI, Request
from dotenv import load_dotenv
from routers import scrapResult, commonInfo
from contextlib import asynccontextmanager
from typing import Dict
from model import MongoDB


@asynccontextmanager
async def initMongo(app: FastAPI):
    MongoDB.client.connect()
    yield
    MongoDB.client.close()


app = FastAPI(lifespan=initMongo, responses={404: {"description": "Not found"}})

app.include_router(scrapResult.router)
app.include_router(commonInfo.router)
