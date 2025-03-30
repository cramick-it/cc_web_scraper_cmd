import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import deque
from typing import List, Dict, Optional
import logging
from web_scraper.database.client import save_page
from web_scraper.entity.models import Page
from web_scraper.config.config import Config


class BaseScraperService:
    def __init__(self, base_url: str, site_id: str):
        self.base_url = base_url
        self.site_id = site_id
        self.visited = set()
        self.queue = deque([base_url])
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': Config.USER_AGENT,
            'Accept-Language': 'en-US,en;q=0.9'
        })
        self.logger = logging.getLogger(__name__)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_resources()

    def close_resources(self):
        """Properly cleanup all resources"""
        try:
            self.session.close()
            self.logger.info("HTTP session closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing session: {str(e)}")

    def normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        return parsed._replace(fragment='', query='').geturl()

    def should_follow_link(self, url: str) -> bool:
        parsed = urlparse(url)
        return (parsed.scheme in ('http', 'https') and
                parsed.netloc == urlparse(self.base_url).netloc and
                not any(url.endswith(ext) for ext in Config.IGNORED_EXTENSIONS))

    def extract_links(self, html: str, current_url: str) -> List[str]:
        soup = BeautifulSoup(html, 'html.parser')
        links = set()

        for a in soup.find_all('a', href=True):
            try:
                href = a['href'].strip()
                if not href or href.startswith(('javascript:', 'mailto:', 'tel:')):
                    continue

                absolute_url = urljoin(current_url, href)
                normalized_url = self.normalize_url(absolute_url)

                if self.should_follow_link(normalized_url):
                    links.add(normalized_url)
            except Exception as e:
                self.logger.warning(f"Error processing link {a}: {str(e)}")

        return list(links)

    def process_page(self, url: str) -> Page:
        try:
            response = self.session.get(
                url,
                timeout=Config.REQUEST_TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            return Page(
                site_id=self.site_id,
                url=url,
                status_code=response.status_code,
                body_html=str(soup),
                body_text=soup.get_text(' ', strip=True),
                links=self.extract_link_metadata(soup),
                error=None,
                meta={}  # Initialize empty meta dict
            )

        except requests.RequestException as e:
            self.logger.error(f"Request failed for {url}: {str(e)}")
            return Page(
                site_id=self.site_id,
                url=url,
                status_code=getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
                body_html=None,
                body_text=None,
                links=[],
                error=str(e),
                meta={}  # Initialize empty meta dict
            )
        except Exception as e:
            self.logger.error(f"Unexpected error processing {url}: {str(e)}")
            return Page(
                site_id=self.site_id,
                url=url,
                status_code=None,
                body_html=None,
                body_text=None,
                links=[],
                error=str(e),
                meta={}  # Initialize empty meta dict
            )

    def extract_link_metadata(self, soup: BeautifulSoup) -> List[Dict]:
        metadata = []
        for a in soup.find_all('a', href=True):
            try:
                metadata.append({
                    'url': a.get('href'),
                    'title': a.get_text(strip=True),
                    'anchor': str(a),
                    'is_external': self.is_external_link(a.get('href', ''))
                })
            except Exception as e:
                self.logger.warning(f"Error extracting link metadata: {str(e)}")
        return metadata

    def is_external_link(self, url: str) -> bool:
        return (urlparse(url).netloc != urlparse(self.base_url).netloc
                and not url.startswith('/'))

    def crawl(self, max_pages: int = 1000):
        try:
            while self.queue and len(self.visited) < max_pages:
                current_url = self.queue.popleft()

                if current_url in self.visited:
                    continue

                self.visited.add(current_url)
                self.logger.info(f"Processing {current_url} (Queue: {len(self.queue)})")

                page_data = self.process_page(current_url)
                save_page(page_data.dict())

                if page_data.error is None:
                    new_links = self.extract_links(page_data.body_html, current_url)
                    self.queue.extend(
                        link for link in new_links
                        if link not in self.visited
                        and link not in self.queue
                    )
        except KeyboardInterrupt:
            self.logger.info("Crawling interrupted by user")
        except Exception as e:
            self.logger.error(f"Crawling failed: {str(e)}")
        finally:
            self.close_resources()
            self.logger.info(f"Crawling completed. Visited {len(self.visited)} pages")