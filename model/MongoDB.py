from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
from dotenv import load_dotenv

load_dotenv()


class MongoDB:
    def __init__(self):
        self.client = None
        self.council_db = None
        self.district_db = None
        self.age_hist_db = None

    def connect(self):
        self.client = AsyncIOMotorClient(os.getenv("MONGO_CONNECTION_URI"))
        self.council_db = AsyncIOMotorDatabase(self.client, "council")
        self.district_db = AsyncIOMotorDatabase(self.client, "district")
        self.age_hist_db = AsyncIOMotorDatabase(self.client, "age_hist")

    def close(self):
        self.client.close()


client = MongoDB()
