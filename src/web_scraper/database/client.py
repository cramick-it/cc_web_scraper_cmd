from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId
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
                cls._instance.db.headings.create_index('page_id')
                cls._instance.db.headings.create_index('parent_id')
                cls._instance.db.files.create_index('page_id')
                cls._instance.db.links.create_index('page_id')
            except PyMongoError as e:
                logger.error(f"Database connection failed: {str(e)}")
                raise
        return cls._instance


def save_page(page_data: dict) -> Optional[ObjectId]:
    try:
        db = DatabaseClient().db
        now = datetime.now()

        # Remove created_at from update if it exists
        page_data.pop('created_at', None)

        result = db.pages.update_one(
            {'url': page_data['url']},
            {'$set': {
                **page_data,
                'updated_at': now
            },
                '$setOnInsert': {
                    'created_at': now
                }},
            upsert=True
        )

        if result.upserted_id:
            logger.info(f"Saved new page: {page_data['url']}")
            return result.upserted_id
        else:
            page = db.pages.find_one({'url': page_data['url']})
            logger.info(f"Updated existing page: {page_data['url']}")
            return page['_id'] if page else None
    except Exception as e:
        logger.error(f"Failed to save page: {str(e)}")
        return None


def save_headings(page_id: ObjectId, headings: List[Dict]) -> bool:
    try:
        db = DatabaseClient().db
        now = datetime.now()

        # First remove old headings for this page
        db.headings.delete_many({'page_id': page_id})

        if headings:
            # Process hierarchy and save headings
            saved_ids = {}
            for heading in headings:
                heading['page_id'] = page_id
                heading['created_at'] = now
                heading['updated_at'] = now

                # If this heading has a parent, set the parent_id
                if 'parent_id' in heading and heading['parent_id'] in saved_ids:
                    heading['parent_id'] = saved_ids[heading['parent_id']]

                result = db.headings.insert_one(heading)
                saved_ids[heading['checksum']] = result.inserted_id

            logger.info(f"Saved {len(saved_ids)} headings for page {page_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to save headings: {str(e)}")
        return False


def save_links(page_id: ObjectId, links: List[Dict]) -> bool:
    try:
        db = DatabaseClient().db
        now = datetime.now()

        # First remove old links for this page
        db.links.delete_many({'page_id': page_id})

        if links:
            links_data = [{
                'url': link['url'],
                'page_id': page_id,
                'title': link.get('title', ''),
                'href': link['href'],
                'created_at': now
            } for link in links]

            result = db.links.insert_many(links_data)
            logger.info(f"Saved {len(result.inserted_ids)} links for page {page_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to save links: {str(e)}")
        return False


def save_files(page_id: ObjectId, files: List[Dict]) -> bool:
    try:
        db = DatabaseClient().db
        now = datetime.now()

        if files:
            files_data = [{
                'url': file['url'],
                'page_id': page_id,
                'title': file.get('title', ''),
                'file_name': file['file_name'],
                'file_extension': file['file_extension'],
                'created_at': now
            } for file in files]

            result = db.files.insert_many(files_data)
            logger.info(f"Saved {len(result.inserted_ids)} files for page {page_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to save files: {str(e)}")
        return False


def get_page(url: str) -> Optional[dict]:
    try:
        db = DatabaseClient().db
        return db.pages.find_one({'url': url})
    except Exception as e:
        logger.error(f"Failed to get page: {str(e)}")
        return None