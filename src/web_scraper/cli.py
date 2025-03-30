import click
import logging
from web_scraper.services.eyewiki_service import EyewikiService
from web_scraper.services.medicalnewstoday_service import MedicalNewsTodayService


@click.group()
def cli():
    pass


@cli.command()
@click.option('--site', type=click.Choice(['eyewiki', 'medicalnewstoday']), required=True)
@click.option('--visible', is_flag=True, help='Only scrape visible text')
@click.option('--limit', type=int, default=5, help='Page limit')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def crawl(site, visible: bool, limit: int, verbose: bool):
    """Main crawl command that matches your existing interface"""
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    service_map = {
        'eyewiki': EyewikiService,
        'medicalnewstoday': MedicalNewsTodayService
    }

    scraper = service_map[site](site_id=site)
    scraper.crawl(max_pages=limit, visible=visible, limit=limit)


def main():
    cli()

if __name__ == '__main__':
    cli()