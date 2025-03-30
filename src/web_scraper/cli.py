import argparse
import logging
from web_scraper.services import MedicalNewsTodayService, EyewikiService
from web_scraper.config.logging_conf import setup_logging

SERVICE_MAP = {
    'medicalnewstoday': MedicalNewsTodayService,
    'eyewiki': EyewikiService
}


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Website Scraper CLI")
    parser.add_argument("--site-id", required=True, help="Unique site identifier")
    parser.add_argument("--service", required=True, choices=SERVICE_MAP.keys(), help="Service to use")
    parser.add_argument("--max-pages", type=int, default=100, help="Maximum pages to crawl")

    args = parser.parse_args()

    try:
        service_class = SERVICE_MAP[args.service]
        with service_class(site_id=args.site_id) as scraper:
            scraper.crawl(max_pages=args.max_pages)
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()