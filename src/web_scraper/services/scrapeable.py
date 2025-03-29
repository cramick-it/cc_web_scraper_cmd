from datetime import datetime
from playwright.async_api import Page
from playwright.async_api import BrowserContext, Browser


class Scrapeable:
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

        page = context.new_page()

        if expand_all:
            await page.goto('about:blank')  # Neophodno za maximize()
            await page.maximize()
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
