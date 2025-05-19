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

```
git clone <https://github.com/ShihabXSarar/Real_Time_Shipment_Tracking_Project>
Create and activate a virtual environment (recommended)

bash
Copy
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

Install Python dependencies
pip install -r requirements.txt

Install Playwright browsers
playwright install
