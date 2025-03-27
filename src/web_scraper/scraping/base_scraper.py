from abc import ABC, abstractmethod
from playwright.sync_api import Page
from typing import Dict, Any

class BaseScraper(ABC):
    @abstractmethod
    def scrape(self, page: Page, url: str) -> Dict[str, Any]:
        """Main scraping method to be implemented by specific scrapers"""
        pass

    def navigate(self, page: Page, url: str):
        """Navigate to the URL and wait for page to load"""
        page.goto(url)
        page.wait_for_load_state("networkidle")