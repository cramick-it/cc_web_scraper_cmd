from bs4 import BeautifulSoup
from urllib.parse import urlparse
from .base_scraper_service import BaseScraperService
from web_scraper.entity.models import Page
import logging


class EyewikiService(BaseScraperService):
    def __init__(self, site_id: str):
        super().__init__(
            base_url="https://eyewiki.org",
            site_id=site_id
        )
        self.logger = logging.getLogger(__name__)

    def process_page(self, url: str) -> Page:
        """Extends base processing with Eyewiki-specific logic"""
        # First call parent class processing
        page_data = super().process_page(url)

        if page_data.error:
            return page_data

        try:
            self.logger.info(f"Processing Eyewiki page: {url}")
            soup = BeautifulSoup(page_data.body_html, 'html.parser')

            # Initialize meta if not exists
            if not hasattr(page_data, 'meta') or not page_data.meta:
                page_data.meta = {}

            # Extract title
            title = soup.find('h1', id='firstHeading')
            if title:
                page_data.meta['title'] = title.get_text(strip=True)
                self.logger.debug(f"Extracted title: {page_data.meta['title']}")

            # Extract main content
            content_div = soup.find('div', id='mw-content-text')
            if content_div:
                # Clean up content
                for element in content_div.find_all(['span', 'div'], class_='mw-editsection'):
                    element.decompose()
                page_data.body_text = content_div.get_text(' ', strip=True)
                self.logger.debug(f"Extracted content length: {len(page_data.body_text)}")

            # Extract categories
            categories = [cat.get_text(strip=True)
                          for cat in soup.select('.mw-normal-catlinks li a')]
            if categories:
                page_data.meta['categories'] = categories
                self.logger.debug(f"Found categories: {categories}")

        except Exception as e:
            self.logger.error(f"Eyewiki processing error: {str(e)}")
            page_data.error = f"Content processing error: {str(e)}"

        return page_data

    def should_follow_link(self, url: str) -> bool:
        """Eyewiki-specific link filtering"""
        parsed = urlparse(url)
        return (super().should_follow_link(url) and
                not parsed.path.startswith(('/Special:', '/File:', '/Talk:')) and
                'action=edit' not in parsed.query)