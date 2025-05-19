import sys
import json
from tracking_parser.scrapers.usps_scraper import USPSScraper
from tracking_parser.scrapers.fedex_scraper import FedExScraper

if __name__ == "__main__":
    # Accept input as a JSON string (from command line or input)
    if len(sys.argv) > 1:
        input_json = sys.argv[1]
    else:
        input_json = input("Enter tracking request as JSON: ")

    try:
        data = json.loads(input_json)
        carrier = data.get("carrier", "").strip().lower()
        tracking_number = data.get("tracking", "").strip()
    except Exception as e:
        print("Invalid input. Please provide JSON: {\"carrier\": \"USPS\" | \"FedEx\", \"tracking\": \"...\"}")
        sys.exit(1)

    if carrier == "usps":
        result = USPSScraper(tracking_number).scrape()
    elif carrier == "fedex":
        result = FedExScraper(tracking_number).scrape()
    else:
        print("Unsupported carrier! Use 'USPS' or 'FedEx'.")
        sys.exit(1)

    print(result.model_dump_json(indent=2))
