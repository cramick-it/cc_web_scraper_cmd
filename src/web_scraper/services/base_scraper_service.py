import asyncio
import hashlib
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import deque
from typing import List, Dict, Optional
import logging
from playwright.async_api import async_playwright
from web_scraper.database.client import save_page, save_headings, get_page
from web_scraper.entity.models import Page, Heading
from web_scraper.config.config import Config
from datetime import datetime


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

    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict]:
        headings = []
        now = datetime.now()
        for i in range(1, 7):  # h1 through h6
            for heading in soup.find_all(f'h{i}'):
                heading_text = heading.get_text(strip=True)
                if heading_text:  # Only include non-empty headings
                    headings.append({
                        'tag': f'h{i}',
                        'title': heading_text,
                        'text': heading_text,
                        'text_html': str(heading),
                        'anchor': str(heading),
                        'level': i,
                        'checksum': self._generate_checksum(str(heading)),
                        'created_at': now,
                        'updated_at': now,
                        'changed_at': now
                    })
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

            # Check if page exists and hasn't changed
            if existing_page and existing_page.get('checksum') == checksum:
                self.logger.info(f"Content unchanged for {url}")
                await page.close()
                await context.close()
                return Page(**existing_page)

            soup = BeautifulSoup(content, 'html.parser')
            headings = self._extract_headings(soup)
            body_text = await page.inner_text('body')

            page_data = Page(
                site_id=self.site_id,
                url=url,
                status_code=status_code,
                content_html=content,
                content_text=body_text,
                headings=headings,
                checksum=checksum
            )

            # Save to database
            save_page(page_data.dict())
            save_headings(url, headings)

            await page.close()
            await context.close()

            return page_data

        except Exception as e:
            self.logger.error(f"Error processing {url}: {str(e)}")
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

                    if not page_data.error:
                        new_links = await self._extract_links(page_data.content_html, current_url)
                        self.queue.extend(
                            link for link in new_links
                            if link not in self.visited
                            and link not in self.queue
                        )
        except Exception as e:
            self.logger.error(f"Crawling failed: {str(e)}")
            raise

    async def _extract_links(self, html: str, current_url: str) -> List[str]:
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if not href or href.startswith(('javascript:', 'mailto:', 'tel:')):
                continue
            absolute_url = urljoin(current_url, href)
            normalized_url = self._normalize_url(absolute_url)
            if self._should_follow_link(normalized_url):
                links.add(normalized_url)
        return list(links)

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        return parsed._replace(fragment='', query='').geturl()

    def _should_follow_link(self, url: str) -> bool:
        parsed = urlparse(url)
        return (parsed.netloc == urlparse(self.base_url).netloc and
                parsed.scheme in ('http', 'https') and
                not any(url.endswith(ext) for ext in Config.IGNORED_EXTENSIONS))