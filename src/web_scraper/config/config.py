import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Browser Settings
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # Database Settings
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB = os.getenv("MONGODB_DB", "web_scraper")

    # Crawler Settings
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    IGNORED_EXTENSIONS = ['.pdf', '.jpg', '.png']