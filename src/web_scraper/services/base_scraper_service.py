import asyncio
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import deque
from typing import List, Dict, Optional
import logging
from playwright.async_api import async_playwright
from web_scraper.database.client import save_page
from web_scraper.entity.models import Page
from web_scraper.config.config import Config


class BaseScraperService:
    def __init__(self, base_url: str, site_id: str, visible: bool = False):
        self.base_url = base_url
        self.site_id = site_id
        self.visible = visible
        self.visited = set()
        self.queue = deque([base_url])
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.playwright = None
        self.browser = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=not self.visible,
            args=['--no-sandbox']
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        return parsed._replace(fragment='', query='').geturl()

    def should_follow_link(self, url: str) -> bool:
        parsed = urlparse(url)
        return (parsed.netloc == urlparse(self.base_url).netloc and
                parsed.scheme in ('http', 'https') and
                not any(url.endswith(ext) for ext in Config.IGNORED_EXTENSIONS))

    async def extract_links(self, html: str, current_url: str) -> List[str]:
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if not href or href.startswith(('javascript:', 'mailto:', 'tel:')):
                continue
            absolute_url = urljoin(current_url, href)
            normalized_url = self.normalize_url(absolute_url)
            if self.should_follow_link(normalized_url):
                links.add(normalized_url)
        return list(links)

    async def process_page(self, url: str) -> Page:
        try:
            context = await self.browser.new_context()
            page = await context.new_page()

            response = await page.goto(url, timeout=15000)
            status_code = response.status if response else 0

            content = await page.content()
            body_text = await page.inner_text('body')

            links = await self.extract_links(content, url)

            page_data = Page(
                site_id=self.site_id,
                url=url,
                status_code=status_code,
                body_html=content,
                body_text=body_text,
                links=links,
                error=None
            )

            await page.close()
            await context.close()

            return page_data
        except Exception as e:
            return Page(
                site_id=self.site_id,
                url=url,
                status_code=0,
                body_html=None,
                body_text=None,
                links=[],
                error=str(e)
            )

    async def crawl(self, max_pages: int = 5):
        try:
            async with self:
                while self.queue and len(self.visited) < max_pages:
                    current_url = self.queue.popleft()
                    if current_url in self.visited:
                        continue

                    self.visited.add(current_url)
                    self.logger.info(f"Processing: {current_url}")

                    page_data = await self.process_page(current_url)
                    save_page(page_data.dict())

                    if not page_data.error:
                        new_links = await self.extract_links(page_data.body_html, current_url)
                        self.queue.extend(
                            link for link in new_links
                            if link not in self.visited
                            and link not in self.queue
                        )
        except Exception as e:
            self.logger.error(f"Crawling failed: {str(e)}")
            raise