from bs4 import BeautifulSoup
from .base_scraper_service import BaseScraperService
from web_scraper.entity.models import Page
import logging
from typing import Optional, Dict


class MedicalNewsTodayService(BaseScraperService):
    def __init__(self, site_id: str, visible: bool = False):
        super().__init__(
            base_url="https://www.medicalnewstoday.com",
            site_id=site_id,
            visible=visible
        )
        self.logger = logging.getLogger(__name__)

    async def process_page_custom(self, url: str) -> Page:
        page_data = await self.process_page(url)

        if page_data.error:
            return page_data

        try:
            soup = BeautifulSoup(page_data.content_html, 'html.parser')

            # Article extraction
            article_div = soup.find('div', attrs={'data-article-body': '0'})
            article = soup.find('article')
            if article:
                # Cleanup
                for element in article.find_all(['script', 'style', 'nav', 'footer', 'aside']):
                    element.decompose()

                    # Main content
                    page_data.body_text = article.get_text(' ', strip=True)

                # Metadata
                title = soup.find('h1')
                published_date = soup.find('time')
                authors = [a.get_text(strip=True) for a in soup.select('.author-name')]
                print(authors)

        except Exception as e:
            self.logger.error(f"MedicalNewsToday processing error: {str(e)}")
            page_data.error = f"Content processing error: {str(e)}"

        return page_data