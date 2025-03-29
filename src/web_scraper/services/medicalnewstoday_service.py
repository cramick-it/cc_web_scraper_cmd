import logging

from playwright.async_api import async_playwright
from pymongo.database import Database
from typing import List
from web_scraper.services.base_scraper_service import BaseScraperService

logger = logging.getLogger(__name__)

class MedicalnewstodayService(BaseScraperService):
    def __init__(self, db: Database):
        self.name = 'MedicalNewsToday'
        self.db = db
        print("✅ Database connection established")
        self.base_url = 'https://www.medicalnewstoday.com'
        self.directory_url = f'{self.base_url}/directory/a-b'

    async def _crawl_directory(self, url: str) -> List[str]:
        await self.load_page(url)
        links = []
        # elements = self.page.locator('.directory-list a').element_handles()
        elements = self.page.locator('a').element_handles()
        for element in elements:
            href = element.get_attribute('href')
            if href and '/articles/' in href:
                links.append(href)
        return links

    async def scrape(self, visible: bool, limit: int):
        print(f"Scraping {self.base_url}")

        # db = get_db()
        # print("✅ Database connection established")

        async with async_playwright() as p:
            # Launch browser with context
            # browser = await p.chromium.launch(headless=not visible)
            browser = await self.launch_browser(p, visible)
            page, context = await self.open_page(browser)
            self.page = page
            print(f"🔍 Starting Medical News Today crawl: {self.directory_url}")
            result = self.update_site_record()


            urls = self._crawl_directory(self.directory_url)

            await self.process_page_urls(browser, context, limit, page, urls)