import click
from web_scraper.services.eyewiki_service import EyewikiService
from web_scraper.services.medicalnewstoday_service import MedicalNewsTodayService


@click.group()
def cli():
    pass


@cli.command()
@click.option('--site', type=click.Choice(['eyewiki', 'medicalnewstoday']), required=True)
@click.option('--visible', is_flag=True, help='Only scrape visible text')
@click.option('--limit', type=int, default=5, help='Page limit')
def crawl(site, visible, limit):
    """Main crawl command that matches your existing interface"""
    service_map = {
        'eyewiki': EyewikiService,
        'medicalnewstoday': MedicalNewsTodayService
    }

    scraper = service_map[site](site_id=site)
    scraper.crawl(max_pages=limit)


def main():
    cli()

if __name__ == '__main__':
    cli()