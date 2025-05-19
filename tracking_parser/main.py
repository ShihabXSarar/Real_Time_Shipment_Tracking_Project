#!/usr/bin/env python3
import json
import argparse
import logging
from typing import Dict, Any, Union, List, Optional
from schemas.tracking import TrackingResponse
from scrapers.usps_scraper import USPSScraper
from scrapers.fedex_scraper import FedExScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_tracking_info(carrier: str, tracking: Union[str, List[str]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    # Handle multiple tracking numbers
    if isinstance(tracking, list):
        results = []
        for track_num in tracking:
            result = get_tracking_info(carrier, track_num)
            results.append(result)
        return results

    # Handle single tracking number
    try:
        # Select and initialize the appropriate scraper
        if carrier.upper() == "USPS":
            scraper = USPSScraper(tracking)
        elif carrier.upper() == "FEDEX":
            scraper = FedExScraper(tracking)
        else:
            return {
                "error": f"Unsupported carrier: {carrier}. Please use 'USPS' or 'FedEx'."
            }

        # Perform the scrape
        logger.info(f"Scraping {carrier} tracking information for {tracking}")
        result = scraper.scrape()

        # Convert to dictionary
        if isinstance(result, TrackingResponse):
            return result.dict()
        else:
            return result

    except Exception as e:
        logger.error(f"Error tracking {carrier} number {tracking}: {str(e)}")
        return {
            "tracking": tracking,
            "carrier": carrier,
            "shipment_status": f"Error: {str(e)}",
            "delivered_at": None,
            "delivery_location": None,
            "route_summary": []
        }


def parse_input(input_data: Union[str, Dict[str, Any]]) -> Dict[str, Union[str, List[str]]]:
    if isinstance(input_data, str):
        try:
            data = json.loads(input_data)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON input")
    else:
        data = input_data

    # Validate input
    if not isinstance(data, dict):
        raise ValueError("Input must be a dictionary")

    if "carrier" not in data:
        raise ValueError("Missing 'carrier' field")

    if "tracking" not in data:
        raise ValueError("Missing 'tracking' field")

    carrier = data["carrier"]
    tracking = data["tracking"]

    # Validate carrier
    if carrier.upper() not in ["USPS", "FEDEX"]:
        raise ValueError("Carrier must be 'USPS' or 'FedEx'")

    # Validate tracking number(s)
    if isinstance(tracking, str):
        # Single tracking number
        if not tracking.strip():
            raise ValueError("Tracking number cannot be empty")
    elif isinstance(tracking, list):
        # Multiple tracking numbers
        if not tracking:
            raise ValueError("Tracking numbers list cannot be empty")
        for track in tracking:
            if not isinstance(track, str) or not track.strip():
                raise ValueError("All tracking numbers must be non-empty strings")
    else:
        raise ValueError("Tracking must be a string or a list of strings")

    return {
        "carrier": carrier,
        "tracking": tracking
    }


def main():
    """Main entry point for command line execution"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Track shipments from USPS and FedEx")
    parser.add_argument("--input", "-i", type=str, help="JSON input string or path to JSON file")
    parser.add_argument("--output", "-o", type=str, help="Path to output JSON file")
    args = parser.parse_args()

    # Get input data
    if args.input:
        # Check if input is a file path
        if args.input.endswith(".json"):
            try:
                with open(args.input, "r") as f:
                    input_data = json.load(f)
            except Exception as e:
                logger.error(f"Error reading input file: {str(e)}")
                return
        else:
            # Assume input is a JSON string
            input_data = args.input
    else:
        # Interactive mode
        print("Enter tracking details as JSON (e.g., {\"carrier\": \"USPS\", \"tracking\": \"1234567890\"}):")
        input_data = input()

    try:
        # Parse input
        parsed_input = parse_input(input_data)

        # Get tracking info
        result = get_tracking_info(parsed_input["carrier"], parsed_input["tracking"])

        # Format output
        output = json.dumps(result, indent=2)

        # Output to file or console
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Results written to {args.output}")
        else:
            print(output)

    except ValueError as e:
        logger.error(f"Input error: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()