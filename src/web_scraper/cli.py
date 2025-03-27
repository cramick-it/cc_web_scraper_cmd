import click
from loguru import logger
from playwright.sync_api import sync_playwright

from web_scraper.config import config
from web_scraper.database.client import get_database
from web_scraper.scraping.site_specific.example_site import scrape_example_site

@click.group()
def cli():
    """Web Scraper CLI Tool"""
    pass

@cli.command()
@click.option("--url", help="URL to scrape", required=True)
def scrape(url):
    """Scrape a website and store data in MongoDB"""
    logger.info(f"Starting scraping for URL: {url}")
    
    db = get_database()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Example scraping - replace with your actual scraping logic
            if "example.com" in url:
                data = scrape_example_site(page, url)
                db.example_data.insert_one(data)
                logger.success("Data successfully scraped and stored")
            else:
                logger.error("Unsupported website")
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    cli()