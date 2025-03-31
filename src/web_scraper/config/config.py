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
    FILE_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']

    # Browser Settings
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    HEADLESS = not bool(os.getenv("SHOW_BROWSER", False))