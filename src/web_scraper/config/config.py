import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # MongoDB Configuration
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB = os.getenv("MONGODB_DB", "web_scraper")
    MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
    MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
    MONGODB_AUTH_SOURCE = os.getenv("MONGODB_AUTH_SOURCE", "admin")

    # Crawler Settings
    REQUEST_TIMEOUT = 30000  # milliseconds
    MAX_PAGES = 1000
    IGNORED_EXTENSIONS = ['.pdf', '.jpg', '.png', '.docx']

    # Content Settings
    MIN_CONTENT_LENGTH = 20  # Minimum characters to consider valid content