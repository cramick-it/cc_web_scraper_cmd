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
            soup = BeautifulSoup(page_data.content_html, 'html.parser')
            content_div = soup.find('div', id='mw-content-text')

            if content_div:
                # Clean up Eyewiki-specific elements
                for element in content_div.find_all(['span', 'div'], class_='mw-editsection'):
                    element.decompose()

                # Update content text
                page_data.content_text = content_div.get_text(' ', strip=True)

        except Exception as e:
            self.logger.error(f"Eyewiki processing error: {str(e)}")
            page_data.error = f"Content processing error: {str(e)}"

        return page_data