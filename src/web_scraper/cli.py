import click
import asyncio
import logging
from web_scraper.services import EyewikiService, MedicalNewsTodayService
from web_scraper.config.logging_conf import setup_logging


@click.group()
def cli():
    pass


@cli.command()
@click.option('--site', type=click.Choice(['eyewiki', 'medicalnewstoday']), required=True)
@click.option('--visible', is_flag=True, help='Run browser in visible mode')
@click.option('--limit', type=int, default=5, help='Page limit')
@click.option('--force', is_flag=True, help='Force re-crawl even if unchanged')
def crawl(site, visible, limit, force):
    """Main crawl command with change detection"""
    setup_logging()

    async def run_crawl():
        service_map = {
            'eyewiki': EyewikiService,
            'medicalnewstoday': MedicalNewsTodayService
        }
        service = service_map[site](site_id=site, visible=visible)
        await service.crawl(max_pages=limit)

    asyncio.run(run_crawl())


if __name__ == '__main__':
    cli()

def main():
    cli()
