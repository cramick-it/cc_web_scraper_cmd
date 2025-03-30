import asyncio
import hashlib
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag
from collections import deque
from typing import List, Dict, Optional
import logging
from playwright.async_api import async_playwright
from web_scraper.database.client import get_page, save_page, update_page
from web_scraper.entity.models import Page, Heading
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

    def _generate_checksum(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    async def _extract_headings(self, soup: BeautifulSoup) -> List[Heading]:
        headings = []
        for i in range(1, 7):
            for h in soup.find_all(f'h{i}'):
                if isinstance(h, Tag):
                    headings.append(Heading(
                        tag=f'h{i}',
                        text=h.get_text(strip=True),
                        anchor=str(h),
                        level=i,
                        checksum=self._generate_checksum(str(h))
                    ))
        return headings

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

    async def process_page(self, url: str) -> Page:
        existing_page = get_page(url)
        try:
            context = await self.browser.new_context()
            page = await context.new_page()

            response = await page.goto(url, timeout=15000)
            status_code = response.status if response else 0

            content = await page.content()
            checksum = self._generate_checksum(content)

            if existing_page and existing_page['checksum'] == checksum:
                update_page(url, {'updated_at': datetime.now()})
                return Page(**existing_page)

            soup = BeautifulSoup(content, 'html.parser')
            headings = await self._extract_headings(soup)
            body_text = await page.inner_text('body')

            page_data = Page(
                site_id=self.site_id,
                url=url,
                status_code=status_code,
                content_html=content,
                content_text=body_text,
                headings=headings,
                links=await self.extract_links(content, url),
                checksum=checksum,
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

                    if page_data.error:
                        save_page(page_data.dict())
                        continue

                    existing_page = get_page(current_url)
                    if existing_page:
                        update_page(current_url, page_data.dict())
                    else:
                        save_page(page_data.dict())

                    new_links = await self.extract_links(page_data.content_html, current_url)
                    self.queue.extend(
                        link for link in new_links
                        if link not in self.visited
                        and link not in self.queue
                    )
        except Exception as e:
            self.logger.error(f"Crawling failed: {str(e)}")
            raise