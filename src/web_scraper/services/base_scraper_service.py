import asyncio
import hashlib
import os
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import deque
from typing import List, Dict, Optional, Tuple
import logging
from playwright.async_api import async_playwright
from web_scraper.database.client import (
    save_page, save_headings, save_links, save_files, get_page
)
from web_scraper.entity.models import Page, PyObjectId
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
        stack = []  # To track heading hierarchy

        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(heading.name[1])
            heading_text = heading.get_text(strip=True)

            if heading_text:
                # Pop stack until we find parent heading
                while stack and stack[-1]['level'] >= level:
                    stack.pop()

                parent_id = stack[-1]['checksum'] if stack else None

                heading_data = {
                    'tag': heading.name,
                    'title': heading_text,
                    'text': heading_text,
                    'text_html': str(heading),
                    'anchor': str(heading),
                    'level': level,
                    'checksum': self._generate_checksum(str(heading)),
                    'parent_id': parent_id
                }

                headings.append(heading_data)
                stack.append(heading_data)

        return headings

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> Tuple[List[Dict], List[Dict]]:
        links = []
        files = []

        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if not href or href.startswith(('javascript:', 'mailto:', 'tel:')):
                continue

            absolute_url = urljoin(base_url, href)
            title = a.get_text(strip=True)

            # Check if it's a file link
            file_ext = os.path.splitext(absolute_url)[1].lower()
            if file_ext in Config.FILE_EXTENSIONS:
                files.append({
                    'url': absolute_url,
                    'title': title,
                    'file_name': os.path.basename(absolute_url),
                    'file_extension': file_ext
                })
            else:
                links.append({
                    'url': absolute_url,
                    'title': title,
                    'href': href
                })

        return links, files

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
            body_text = await page.inner_text('body')

            # Extract all data
            headings = self._extract_headings(soup)
            links, files = self._extract_links(soup, url)

            # Save page and get its ID
            page_data = Page(
                site_id=self.site_id,
                url=url,
                status_code=status_code,
                content_html=content,
                content_text=body_text,
                checksum=checksum
            )

            page_id = save_page(page_data.dict())

            if page_id:
                # Save related data
                save_headings(page_id, headings)
                save_links(page_id, links)
                save_files(page_id, files)

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
                        new_links, _ = self._extract_links(
                            BeautifulSoup(page_data.content_html, 'html.parser'),
                            current_url
                        )
                        self.queue.extend(
                            link['url'] for link in new_links
                            if link['url'] not in self.visited
                            and link['url'] not in self.queue
                            and self._should_follow_link(link['url'])
                        )
        except Exception as e:
            self.logger.error(f"Crawling failed: {str(e)}")
            raise

    def _should_follow_link(self, url: str) -> bool:
        parsed = urlparse(url)
        return (parsed.netloc == urlparse(self.base_url).netloc and
                parsed.scheme in ('http', 'https') and
                not any(url.endswith(ext) for ext in Config.IGNORED_EXTENSIONS))