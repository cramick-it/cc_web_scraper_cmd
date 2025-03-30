from urllib.parse import urlparse

from bs4 import BeautifulSoup
from .base_scraper_service import BaseScraperService
from web_scraper.entity.models import Page
import logging
from typing import Optional, Dict


class EyewikiService(BaseScraperService):
    def __init__(self, site_id: str):
        super().__init__(
            base_url="https://eyewiki.org",
            site_id=site_id
        )
        self.logger = logging.getLogger(__name__)
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml',
            'Referer': self.base_url
        })

    def process_page(self, url: str) -> Page:
        """Eyewiki-specific page processing"""
        page_data = super().process_page(url)

        if page_data.body_html and not page_data.error:
            try:
                soup = BeautifulSoup(page_data.body_html, 'html.parser')

                # Main content extraction
                content_div = soup.find('div', {'id': 'mw-content-text'})
                if content_div:
                    # Remove edit sections and other noise
                    for element in content_div.find_all(['span', 'div'], class_='mw-editsection'):
                        element.decompose()

                    # Clean tables
                    for table in content_div.find_all('table'):
                        table.decompose() if 'infobox' in table.get('class', []) else None

                    page_data.body_text = content_div.get_text(' ', strip=True)

                    # Extract metadata
                    title = soup.find('h1', {'id': 'firstHeading'})
                    contributors = [a.get_text(strip=True) for a in soup.select('.mw-contributors li a')]
                    last_updated = soup.find('li', {'id': 'footer-info-lastmod'})

                    page_data.meta = {
                        'title': title.get_text(strip=True) if title else None,
                        'contributors': contributors,
                        'last_updated': last_updated.get_text(strip=True) if last_updated else None,
                        'categories': [c.get_text(strip=True) for c in soup.select('.mw-normal-catlinks li a')]
                    }

            except Exception as e:
                self.logger.error(f"Eyewiki processing error: {str(e)}")
                page_data.error = f"Content processing error: {str(e)}"

        return page_data

    def should_follow_link(self, url: str) -> bool:
        """Override for Eyewiki-specific link filtering"""
        parsed = urlparse(url)
        return (super().should_follow_link(url) and
                not parsed.path.startswith(('/Special:', '/File:', '/Talk:')) and
                'action=edit' not in parsed.query)