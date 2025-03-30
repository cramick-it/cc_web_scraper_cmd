import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # HTTP Configuration
    USER_AGENT = "Mozilla/5.0 (compatible; WebScraper/1.0)"
    REQUEST_TIMEOUT = 15
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    # Crawling Configuration
    MAX_PAGES = 1000
    IGNORED_EXTENSIONS = ['.pdf', '.jpg', '.png', '.doc', '.docx', '.mp4']
    CRAWL_DELAY = 1.0  # Seconds between requests

    # Database Configuration
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB = os.getenv("MONGODB_DB", "web_scraper")

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = "logs/scraper.log"