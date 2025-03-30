from bs4 import BeautifulSoup
from web_scraper.services.base_scraper_service import BaseScraperService
from web_scraper.entity.models import Page
import logging


class EyewikiService(BaseScraperService):
    def __init__(self, site_id: str, visible: bool = False):
        super().__init__(
            base_url="https://eyewiki.org",
            site_id=site_id,
            visible=visible
        )
        self.logger = logging.getLogger(__name__)

    async def process_page(self, url: str) -> Page:
        page_data = await super().process_page(url)

        if page_data.error:
            return page_data

        try:
            soup = BeautifulSoup(page_data.body_html, 'html.parser')

            # Initialize meta if not exists
            if not hasattr(page_data, 'meta'):
                page_data.meta = {}

            # Extract title
            title = soup.find('h1', id='firstHeading')
            if title:
                page_data.meta['title'] = title.get_text(strip=True)

            # Extract main content
            content_div = soup.find('div', id='mw-content-text')
            if content_div:
                for element in content_div.find_all(['span', 'div'], class_='mw-editsection'):
                    element.decompose()
                page_data.body_text = content_div.get_text(' ', strip=True)

            # Extract categories
            categories = [cat.get_text(strip=True)
                          for cat in soup.select('.mw-normal-catlinks li a')]
            if categories:
                page_data.meta['categories'] = categories

        except Exception as e:
            self.logger.error(f"Eyewiki processing error: {str(e)}")
            page_data.error = f"Content processing error: {str(e)}"

        return page_data