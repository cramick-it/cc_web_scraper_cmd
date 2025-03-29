import asyncio

import click

from web_scraper.database.client import get_db
from web_scraper.services.eyewiki_service import EyewikiService

from web_scraper.services.medicalnewstoday_service import MedicalnewstodayService
from web_scraper.utils.logging import configure_logging

logger = configure_logging()


@click.group()
def cli():
    """Web Scraper CLI Tool"""
    pass


def main():
    cli()


@cli.command()
@click.option('--site', type=click.Choice(['eyewiki', 'medicalnewstoday']), required=True)
@click.option('--visible', is_flag=True, help='Run browser in visible mode')
@click.option('--limit', type=int, default=5, help='Limit number of pages to scrape')
def crawl(site: str, visible: bool, limit: int):
    async def _run():
        db = get_db()
        if site == 'eyewiki':
            eyewiki_service = EyewikiService(db)
            await eyewiki_service.scrape(visible, limit)
        elif site == 'medicalnewstoday':
            medicalnewstoday_service = MedicalnewstodayService(db)
            await medicalnewstoday_service.scrape(visible, limit)
        else:
            click.echo(f"Unknown site: {site}")

    asyncio.run(_run())



if __name__ == '__main__':
    cli()