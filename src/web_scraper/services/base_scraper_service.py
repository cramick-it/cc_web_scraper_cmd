from hashlib import md5
from datetime import datetime
from typing import List, Dict, Optional
from playwright.async_api import Page
from bs4 import BeautifulSoup


class BaseScraperService:
    def __init__(self, page: Page):
        self.page = page
        self.soup = None

    async def load_page(self, url: str):
        await self.page.goto(url, wait_until="networkidle")
        self.soup = BeautifulSoup(self.page.content(), 'html.parser')

    async def get_page_data(self, url: str) -> Dict:
        await self.load_page(url)

        title = self.page.title()
        headings = self.extract_headings()
        body_text = self.extract_body_text()

        return {
            "url": url,
            "title": title,
            "body": body_text,
            "date": datetime.utcnow(),
            "change_verifier": self.generate_change_verifier(title, headings),
            "headings": headings
        }

    def extract_headings(self) -> List[Dict]:
        headings = []
        for i, tag in enumerate(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            for j, element in enumerate(self.soup.find_all(tag)):
                headings.append({
                    "tag": tag,
                    "text": element.get_text(strip=True),
                    "order": j + 1,
                    "level": i + 1,
                    "position": len(headings) + 1
                })
        return headings

    def extract_body_text(self) -> str:
        # Remove script and style elements
        for script in self.soup(["script", "style"]):
            script.decompose()
        return self.soup.get_text(' ', strip=True)

    def generate_change_verifier(self, title: str, headings: List[Dict]) -> str:
        content = title + ''.join(h['text'] for h in headings)
        return md5(content.encode('utf-8')).hexdigest()