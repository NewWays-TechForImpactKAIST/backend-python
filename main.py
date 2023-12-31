from fastapi import FastAPI, Request
from dotenv import load_dotenv
from routers import (
    commonInfo,
    ageHist,
    scrapResultLocal,
    scrapResultMetro,
    scrapResultNational,
)
from contextlib import asynccontextmanager
from typing import Dict
from model import MongoDB
from model.ResponseType import ChartResponse, GenderInfo, PartyInfo, AgeInfo
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def initMongo(app: FastAPI):
    MongoDB.client.connect()
    yield
    MongoDB.client.close()


new = ChartResponse[GenderInfo]

app = FastAPI(lifespan=initMongo, responses={404: {"description": "Not found"}})

origin = [
    "http://localhost:5173",
    "https://diversity.tech4impact.kr",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origin,
    allow_origin_regex="https://.*\.netlify\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scrapResultLocal.router)
app.include_router(scrapResultMetro.router)
app.include_router(scrapResultNational.router)
app.include_router(commonInfo.router)
app.include_router(ageHist.router)
