import logging
from datetime import datetime

from playwright.async_api import async_playwright
from pymongo.database import Database
from typing import List
from urllib.parse import urljoin
from web_scraper.services.base_scraper_service import BaseScraperService

logger = logging.getLogger(__name__)

class EyewikiService(BaseScraperService):
    def __init__(self, db: Database):
        self.name = 'EyeWiki'
        self.db = db
        print("✅ Database connection established")
        self.base_url = 'https://eyewiki.org'
        self.category_url = f'{self.base_url}/Category:Articles'

    async def _crawl_category(self, url: str) -> List[str]:
        await self.load_page(url)
        links = []
        # Koristite Playwright selektor umesto BeautifulSoup
        # link_elements = self.page.query_selector_all('.category-page__member-link')
        link_elements = await self.page.query_selector_all('a')
        print(f"Found {len(link_elements)} link elements")

        for element in link_elements:
            href = await element.get_attribute('href')
            if href:
                if href.startswith("//") or (href.lower().startswith("http") and not href.lower().startswith(url.lower())):
                    print(f"Skipping {href}")
                    continue
                full_url = urljoin(url, href)
                print(f"Processing link: {full_url}")
                links.append(full_url)

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
            print(f"🔍 Starting EyeWiki crawl: {self.category_url}")
            result = self.update_site_record()

            # Get article links
            print("🔄 Collecting article links...")
            # urls = scraper.crawl_category(self.category_url)
            urls = await self._crawl_category(self.category_url)
            print(f"📊 Found {len(urls)} articles")

            await self.process_page_urls(browser, context, limit, page, urls)

