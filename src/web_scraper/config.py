import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "scraper_db")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

config = Config()
