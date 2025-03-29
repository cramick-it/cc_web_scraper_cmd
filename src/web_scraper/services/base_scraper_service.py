from hashlib import md5
from typing import List, Dict
from bs4 import BeautifulSoup
from datetime import datetime
from playwright.async_api import Page, Playwright
from playwright.async_api import BrowserContext, Browser


class BaseScraperService:
    def __init__(self, page: Page):
        self.page = page
        self.soup = None

    async def launch_browser(self, p: Playwright, visible: bool):
        # Launch browser with context
        # browser = await p.chromium.launch(headless=not visible)
        browser = await p.chromium.launch(
            headless=not visible,
            args=[
                '--start-maximized',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ]
        )

        return browser

    async def close_resources(self, page: Page, context: BrowserContext, browser: Browser):
        await page.close()
        await context.close()
        await browser.close()
        print("✅ Crawling completed!")

    def handle_error(self, e: Exception, url: str):
        print(f"❌ Error processing {url}: {str(e)}")
        self.db.pages.update_one(
            {'url': url},
            {'$set': {
                'status': 'error',
                'error': str(e),
                'visited_at': datetime.utcnow()
            }},
            upsert=True
        )

    async def open_page(self, browser: Browser, expand_all: bool = True):
        """Kreira novu stranicu sa kontekstom"""
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 1024} if not expand_all else None,
            locale='en-US',
            java_script_enabled=True,
            ignore_https_errors=True
        )

        page = await context.new_page()

        if expand_all:
            await page.goto('about:blank')  # Neophodno za maximize()
            # await page.maximize()
            viewport_size = page.viewport_size
            print(f"🌐 Browser maximized to: {viewport_size['width']}x{viewport_size['height']}")
        else:
            print("🌐 Browser launched with fixed size: 1280x1024")

        return page, context


    def get_site_record(self, home_url: str):
        site_record = self.db.sites.find_one({'home_url': home_url})

        if not site_record:
            raise ValueError(f"Site with home URL {home_url} not found")

        print(f"🏷️ Site ID: {site_record['_id']}")
        return site_record

    def update_site_record(self):
        result = self.db.sites.update_one(
            {'home_url': self.base_url},
            {'$set': {
                'name': self.name,
                'updated_at': datetime.utcnow(),
                'last_crawl': datetime.utcnow()
            }},
            upsert=True
        )
        return result


    async def load_page(self, url: str):
        await self.page.goto(url, wait_until="networkidle")
        page_content = await self.page.content()
        self.soup = BeautifulSoup(page_content, 'html.parser')

    async def get_page_data(self, url: str) -> Dict:
        await self.load_page(url)

        title = await self.page.title()
        headings = self.extract_headings()
        body_text = self.extract_body_text()

        return {
            "url": url,
            "title": title,
            "body": body_text,
            "date": datetime.utcnow(),
            "change_verifier": self.generate_change_verifier(title, headings),
            "headings": headings
        }

    def extract_headings(self) -> List[Dict]:
        headings = []
        for i, tag in enumerate(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            for j, element in enumerate(self.soup.find_all(tag)):
                headings.append({
                    "tag": tag,
                    "text": element.get_text(strip=True),
                    "order": j + 1,
                    "level": i + 1,
                    "position": len(headings) + 1
                })
        return headings

    def extract_body_text(self) -> str:
        # Remove script and style elements
        for script in self.soup(["script", "style"]):
            script.decompose()
        return self.soup.get_text(' ', strip=True)

    def generate_change_verifier(self, title: str, headings: List[Dict]) -> str:
        content = title + ''.join(h['text'] for h in headings)
        return md5(content.encode('utf-8')).hexdigest()

    async def process_page_urls(self, browser, context, limit, page, urls):
        # Apply limit
        urls = urls[:limit]
        print(f"🔧 Processing first {len(urls)} URLs")
        # site_record = self.db.sites.find_one({'home_url': self.base_url})
        # print(f"🏷️ Site ID: {site_record['_id']}")
        site_record = self.get_site_record(self.base_url)
        for i, url in enumerate(urls, 1):
            print(f"\n⏳ Processing {i}/{len(urls)}: {url}")
            try:
                page_data = await self.get_page_data(url)
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