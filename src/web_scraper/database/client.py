from pymongo import MongoClient
from web_scraper.config.config import Config
import logging

logger = logging.getLogger(__name__)

def get_db_client():
    client = MongoClient(
        Config.MONGODB_URI,
        username='root',
        password='topsecret',
        authSource='admin',
        authMechanism='SCRAM-SHA-256'
    )
    return client[Config.MONGODB_DB]

def save_page(page_data: dict):
    try:
        with get_db_client() as client:
            db = client[Config.MONGODB_DB]
            result = db.pages.insert_one(page_data)
            logger.info(f"Saved page: {page_data['url']}")
            return result.inserted_id
    except Exception as e:
        logger.error(f"Failed to save page: {str(e)}")
        return None