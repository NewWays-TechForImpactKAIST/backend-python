from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
    
    def connect(self):
        self.client = AsyncIOMotorClient(os.getenv("MONGO_CONNECTION_URI"))
        self.db = AsyncIOMotorDatabase(self.client, os.getenv("MONGO_DATABASE"))

    def close(self):
        self.client.close()

client = MongoDB()
