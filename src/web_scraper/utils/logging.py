from loguru import logger

def configure_logging():
    logger.add("logs/scraper.log", rotation="10 MB", retention="10 days")
    return logger