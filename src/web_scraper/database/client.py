from pymongo import MongoClient
from pymongo.database import Database

from web_scraper.config.config import Config


def get_db() -> Database:
    client = MongoClient(
        Config.MONGO_URI,
        username='root',
        password='topsecret',
        authSource='admin',
        authMechanism='SCRAM-SHA-256'
    )
    return client[Config.MONGO_DB_NAME]