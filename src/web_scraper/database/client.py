from pymongo import MongoClient
from pymongo.errors import PyMongoError
from web_scraper.config.config import Config
from web_scraper.entity.models import Page
import logging


class DatabaseClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.db = None

    def __enter__(self):
        try:
            self.client = MongoClient(
                Config.MONGODB_URI,
                username='root',
                password='topsecret',
                authSource='admin',
                authMechanism='SCRAM-SHA-256',
                connectTimeoutMS=30000,
                socketTimeoutMS=30000
            )
            self.db = self.client[Config.MONGODB_DB]
            return self
        except PyMongoError as e:
            self.logger.error(f"Database connection failed: {str(e)}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            try:
                self.client.close()
                self.logger.info("MongoDB connection closed")
            except Exception as e:
                self.logger.error(f"Error closing database connection: {str(e)}")

    def save_page(self, page_data: dict):
        try:
            result = self.db.pages.insert_one(page_data)
            self.logger.debug(f"Inserted page {page_data['url']} with ID {result.inserted_id}")
            return result.inserted_id
        except PyMongoError as e:
            self.logger.error(f"Failed to save page {page_data.get('url')}: {str(e)}")
            return None


# Singleton instance
db_client = DatabaseClient()


def save_page(page_data: dict):
    with db_client as client:
        return client.save_page(page_data)