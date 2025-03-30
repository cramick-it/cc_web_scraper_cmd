from pymongo import MongoClient, ReturnDocument
from pymongo.errors import PyMongoError
from web_scraper.config.config import Config
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_client = None

def get_client():
    global _client
    if _client is None:
        try:
            _client = MongoClient(
                Config.MONGODB_URI,
                username=Config.MONGODB_USERNAME,
                password=Config.MONGODB_PASSWORD,
                authSource=Config.MONGODB_AUTH_SOURCE,
                connectTimeoutMS=30000
            )
        except PyMongoError as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
    return _client

def get_db():
    return get_client()[Config.MONGODB_DB]

def get_page(url: str) -> dict:
    try:
        return get_db().pages.find_one({'url': url})
    except PyMongoError as e:
        logger.error(f"Failed to get page {url}: {str(e)}")
        return None

def save_page(page_data: dict):
    try:
        result = get_db().pages.insert_one(page_data)
        logger.info(f"Saved new page: {page_data['url']}")
        return result.inserted_id
    except PyMongoError as e:
        logger.error(f"Failed to save page {page_data.get('url')}: {str(e)}")
        return None

def update_page(url: str, updates: dict):
    try:
        updates['updated_at'] = datetime.now()
        result = get_db().pages.find_one_and_update(
            {'url': url},
            {'$set': updates},
            return_document=ReturnDocument.AFTER
        )
        if result:
            logger.info(f"Updated page: {url}")
        return result
    except PyMongoError as e:
        logger.error(f"Failed to update page {url}: {str(e)}")
        return None

def save_heading(url: str, heading: dict):
    try:
        result = get_db().headings.update_one(
            {'url': url, 'heading.checksum': heading['checksum']},
            {'$set': {'heading': heading, 'updated_at': datetime.now()}},
            upsert=True
        )
        logger.debug(f"Saved heading for {url}")
        return result.upserted_id
    except PyMongoError as e:
        logger.error(f"Failed to save heading for {url}: {str(e)}")
        return None