# src/web_scraper/__init__.py
from web_scraper.services.eyewiki_service import EyewikiService
from web_scraper.services.medicalnewstoday_service import MedicalNewsTodayService

__all__ = ['EyewikiService', 'MedicalNewsTodayService']