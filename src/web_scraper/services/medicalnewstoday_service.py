from bs4 import BeautifulSoup
from .base_scraper_service import BaseScraperService
from web_scraper.entity.models import Page
import logging
from typing import Optional, Dict


class MedicalNewsTodayService(BaseScraperService):
    def __init__(self, site_id: str):
        super().__init__(
            base_url="https://www.medicalnewstoday.com",
            site_id=site_id
        )
        self.logger = logging.getLogger(__name__)

    def process_page(self, url: str) -> Page:
        """MedicalNewsToday-specific page processing"""
        page_data = super().process_page(url)

        if page_data.body_html and not page_data.error:
            try:
                soup = BeautifulSoup(page_data.body_html, 'html.parser')

                # Article extraction
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

                    page_data.meta = {
                        'title': title.get_text(strip=True) if title else None,
                        'published_date': published_date['datetime'] if published_date and published_date.has_attr(
                            'datetime') else None,
                        'authors': authors,
                        'categories': [c.get_text(strip=True) for c in soup.select('.article-taxonomies__link')]
                    }

            except Exception as e:
                self.logger.error(f"MedicalNewsToday processing error: {str(e)}")
                page_data.error = f"Content processing error: {str(e)}"

        return page_data