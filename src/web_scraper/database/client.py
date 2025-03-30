from pymongo import MongoClient
from pymongo.errors import PyMongoError
from web_scraper.config.config import Config
import logging

logger = logging.getLogger(__name__)


class DatabaseClient:
    def __init__(self):
        self.client = None
        self.db = None

    def connect(self):
        try:
            self.client = MongoClient(
                Config.MONGODB_URI,
                username=Config.MONGODB_USERNAME,
                password=Config.MONGODB_PASSWORD,
                authSource=Config.MONGODB_AUTH_SOURCE,
                connectTimeoutMS=30000
            )
            self.db = self.client[Config.MONGODB_DB]
            return self
        except PyMongoError as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise

    def close(self):
        if self.client:
            try:
                self.client.close()
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")


def save_page(page_data: dict):
    db_client = DatabaseClient()
    try:
        db_client.connect()
        result = db_client.db.pages.insert_one(page_data)
        logger.info(f"Saved page: {page_data['url']}")
        return result.inserted_id
    except PyMongoError as e:
        logger.error(f"Failed to save page {page_data.get('url')}: {str(e)}")
        return None
    finally:
        db_client.close()