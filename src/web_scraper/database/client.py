from pymongo import MongoClient
from pymongo.database import Database
from web_scraper.config import config

class MongoDBClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
            cls._instance.client = MongoClient(config.MONGO_URI)
        return cls._instance

    def get_db(self) -> Database:
        return self.client[config.MONGO_DB_NAME]

def get_database() -> Database:
    return MongoDBClient().get_db()