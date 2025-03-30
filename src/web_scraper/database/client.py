from pymongo import MongoClient
from pymongo.errors import PyMongoError
from web_scraper.config.config import Config
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class DatabaseClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            try:
                cls._instance.client = MongoClient(
                    Config.MONGODB_URI,
                    username=Config.MONGODB_USERNAME,
                    password=Config.MONGODB_PASSWORD,
                    authSource=Config.MONGODB_AUTH_SOURCE,
                    connectTimeoutMS=30000
                )
                cls._instance.db = cls._instance.client[Config.MONGODB_DB]
                # Create indexes
                cls._instance.db.pages.create_index('url', unique=True)
                cls._instance.db.headings.create_index('url')
                cls._instance.db.headings.create_index('checksum')
            except PyMongoError as e:
                logger.error(f"Database connection failed: {str(e)}")
                raise
        return cls._instance


def save_page(page_data: dict) -> bool:
    try:
        db = DatabaseClient().db
        now = datetime.now()

        # Remove created_at from update if it exists
        page_data.pop('created_at', None)

        update_data = {
            '$set': {
                **page_data,
                'updated_at': now,
                'changed_at': now
            },
            '$setOnInsert': {
                'created_at': now
            }
        }

        result = db.pages.update_one(
            {'url': page_data['url']},
            update_data,
            upsert=True
        )

        if result.upserted_id:
            logger.info(f"Saved new page: {page_data['url']}")
        else:
            logger.info(f"Updated existing page: {page_data['url']}")
        return True
    except Exception as e:
        logger.error(f"Failed to save page: {str(e)}")
        return False


def save_headings(url: str, headings: List[Dict]) -> bool:
    try:
        db = DatabaseClient().db
        now = datetime.now()

        # First remove old headings
        db.headings.delete_many({'url': url})

        # Insert new ones if they exist
        if headings:
            # Add metadata to each heading
            headings_with_meta = []
            for h in headings:
                heading_data = {
                    **h,
                    'url': url,
                    'created_at': now,
                    'updated_at': now,
                    'changed_at': now
                }
                headings_with_meta.append(heading_data)

            result = db.headings.insert_many(headings_with_meta)
            logger.info(f"Saved {len(result.inserted_ids)} headings for {url}")
        return True
    except Exception as e:
        logger.error(f"Failed to save headings: {str(e)}")
        return False


def get_page(url: str) -> Optional[dict]:
    try:
        db = DatabaseClient().db
        return db.pages.find_one({'url': url})
    except Exception as e:
        logger.error(f"Failed to get page: {str(e)}")
        return None