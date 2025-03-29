import logging
from datetime import datetime

from playwright.async_api import async_playwright
from pymongo.database import Database
from typing import List
from urllib.parse import urljoin
from web_scraper.services.base_scraper_service import BaseScraperService
from web_scraper.services.scrapeable import Scrapeable

logger = logging.getLogger(__name__)

class EyewikiService(BaseScraperService, Scrapeable):
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
        link_elements = self.page.query_selector_all('a')
        print(f"Found {len(link_elements)} link elements")

        for element in link_elements:
            href = element.get_attribute('href')
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
            browser = await p.chromium.launch(headless=not visible)
            page, context = await self.open_page(browser)
            self.page = page
            print(f"🔍 Starting EyeWiki crawl: {self.category_url}")
            result = self.update_site_record()

            # Get article links
            print("🔄 Collecting article links...")
            # urls = scraper.crawl_category(self.category_url)
            urls = await self._crawl_category(self.category_url)
            print(f"📊 Found {len(urls)} articles")

            # Apply limit
            urls = urls[:limit]
            print(f"🔧 Processing first {len(urls)} URLs")

            # site_record = self.db.sites.find_one({'home_url': self.base_url})
            # print(f"🏷️ Site ID: {site_record['_id']}")
            site_record = self.get_site_record(self.base_url)

            for i, url in enumerate(urls, 1):
                print(f"\n⏳ Processing {i}/{len(urls)}: {url}")
                try:
                    page_data = self.get_page_data(url)
                    print(f"📄 Page title: {page_data['title']}")

                    # Save page
                    result = self.db.pages.update_one(
                        {'url': url},
                        {'$set': {
                            'site_id': site_record['_id'],
                            'title': page_data['title'],
                            'body': page_data['body'],
                            'date': page_data['date'],
                            'change_verifier': page_data['change_verifier'],
                            'visited_at': datetime.utcnow(),
                            'status': 'success'
                        }},
                        upsert=True
                    )
                    print(f"💾 Saved page: {result.raw_result}")

                    # Save headings
                    page_id = result.upserted_id or self.db.pages.find_one({'url': url})['_id']
                    self.db.headings.delete_many({'page_id': page_id})

                    for heading in page_data['headings']:
                        heading['page_id'] = page_id
                        self.db.headings.insert_one(heading)
                    print(f"📌 Saved {len(page_data['headings'])} headings")

                except Exception as e:
                    self.handle_error(e, url)

            # Zatvaranje resursa
            await self.close_resources(page, context, browser)

