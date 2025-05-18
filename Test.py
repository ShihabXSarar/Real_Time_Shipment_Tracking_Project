from tracking_parser.scrapers.usps_scraper import USPSScraper
from tracking_parser.scrapers.fedex_scraper import FedExScraper
"""
# Test USPS
usps_result = USPSScraper("9405503699300745053865").scrape()
print("USPS Result:", usps_result.model_dump_json(indent=2))
"""
fedex_result = FedExScraper("880808205249").scrape()
print("FedEx Result:", fedex_result.model_dump_json(indent=2))