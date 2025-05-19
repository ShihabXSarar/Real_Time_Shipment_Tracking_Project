# Real-Time Shipment Tracking Parser

This project provides a real-time shipment tracking parser for USPS and FedEx using browser automation and HTML parsing. It fetches live tracking data from official carrier websites and returns a standardized JSON output with detailed shipment status and event history.

---

## Features

- Supports USPS and FedEx tracking.
- Uses Playwright for browser automation to handle JavaScript-rendered pages.
- Parses detailed tracking history and delivery status.
- Returns consistent, structured JSON output.
- No use of paid third-party APIs.

---

## Requirements

- Python 3.8 or higher
- [Playwright](https://playwright.dev/python/)
- Additional Python packages listed in `requirements.txt`

---

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/ShihabXSarar/Real_Time_Shipment_Tracking_Project
cd Real_Time_Shipment_Tracking_Project

````

2. **Create and activate a virtual environment (recommended)**

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

4. **Install Playwright browsers**

```bash
playwright install
```

---

## Usage

The script accepts JSON input specifying the carrier and tracking number, and returns tracking details.

### Command-line usage

Run the script with a JSON string argument:

```bash
python Test.py '{"carrier": "FedEx", "tracking": "880646011093"}'
```

or

```bash
python Test.py '{"carrier": "USPS", "tracking": "9405503699300745053865"}'
```

### Interactive usage

Run the script without arguments to input JSON interactively:

```bash
python Test.py
```

Then enter a JSON object, e.g.:

```json
{"carrier": "FedEx", "tracking": "880646011093"}
```

---

## Input Format

```json
{
  "carrier": "USPS" | "FedEx",
  "tracking": "<tracking_number_string>"
}
```

---

## Output Format

```json
{
  "tracking": "<tracking_number>",
  "carrier": "USPS" | "FedEx",
  "shipment_status": "<Shipment status>",
  "delivered_at": "<Delivery timestamp or null>",
  "delivery_location": "<Delivery location or null>",
  "route_summary": [
    {
      "event": "<Event name>",
      "location": "<Event location>",
      "datetime": "<Event timestamp>",
      "note": "<Optional note>"
    }
    // More events ...
  ]
}
```

---

## Project Structure

* `tracking_parser/scrapers/`
  Contains carrier-specific scraper implementations (`usps_scraper.py`, `fedex_scraper.py`).

* `Test.py`
  Entry point script to run the tracking parser with JSON input.

* `requirements.txt`
  Python package dependencies.

---

## Notes

* Ensure you have a stable internet connection; the scraper loads live carrier web pages.
* Use Python 3.8+ for compatibility.
* Playwright installs browser binaries on first run; ensure `playwright install` is executed.


## Contact

For any questions or issues, don't hesitate to get in touch with \Shihab Sarar at \[[shihab312417@gmail.com](mailto:shihab312417@gmail.com)].
