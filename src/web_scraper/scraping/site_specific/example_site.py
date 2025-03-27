from datetime import datetime, timezone
from playwright.sync_api import Page
from typing import Dict
from web_scraper.scraping.base_scraper import BaseScraper


class ExampleSiteScraper(BaseScraper):
    def scrape(self, page: Page, url: str) -> Dict:
        self.navigate(page, url)

        # Example scraping logic
        title = page.title()
        heading = page.inner_text("h1")

        return {
            "url": url,
            "title": title,
            "heading": heading,
            "scraped_at": datetime.now(timezone.utc)  # Ispravljeno
        }


def scrape_example_site(page: Page, url: str) -> Dict:
    scraper = ExampleSiteScraper()
    return scraper.scrape(page, url)