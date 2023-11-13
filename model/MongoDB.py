from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
    
    def connect(self):
        self.client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
        self.db = AsyncIOMotorDatabase(self.client, os.getenv("MONGO_DB"))

    def close(self):
        self.client.close()

client = MongoDB()
