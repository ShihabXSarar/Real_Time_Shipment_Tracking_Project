from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import random
import time
import logging
from fake_useragent import UserAgent
from ..schemas.tracking import TrackingResponse, TrackingEvent
from .base_scraper import BaseScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FedExScraper(BaseScraper):
    """FedEx scraper using 'Track Another Shipment' and robust selectors."""

    def __init__(self, tracking_number: str):
        super().__init__(tracking_number)
        self.ua = UserAgent()
        self.user_agent = self.ua.random
        self.max_retries = 3
        self.current_retry = 0
        self.tracking_url = "https://www.fedex.com/fedextrack/"

    def _human_like_delay(self):
        base_delay = random.uniform(1.0, 2.5)
        delay = base_delay * (1.5 ** self.current_retry)
        logger.info(f"Human-like delay: {delay:.2f}s")
        time.sleep(delay)

    def _stealth_browser_setup(self, page):
        page.evaluate("""() => {
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}, app: {}};
            Object.defineProperty(navigator, 'plugins', {get: () => [{0: {type: "application/x-google-chrome-pdf"}, description: "Portable Document Format", filename: "internal-pdf-viewer", length: 1, name: "Chrome PDF Plugin"}]});
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ? Promise.resolve({state: Notification.permission}) : originalQuery(parameters)
            );
        }""")

    def scrape(self) -> TrackingResponse:
        while self.current_retry < self.max_retries:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-infobars",
                            "--window-size=1920,1080",
                        ],
                        slow_mo=120
                    )
                    context = browser.new_context(
                        user_agent=self.user_agent,
                        viewport={"width": 1920, "height": 1080},
                        locale="en-US",
                        timezone_id="America/New_York",
                        java_script_enabled=True,
                        has_touch=False
                    )
                    try:
                        page = context.new_page()
                        self._stealth_browser_setup(page)
                        page.set_default_timeout(90000)

                        page.route('**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,eot}', lambda route: route.abort())
                        logger.info(f"Navigating to FedEx page for {self.tracking_number}...")
                        page.goto(self.tracking_url, wait_until="networkidle", timeout=90000)
                        self._human_like_delay()
                        page.wait_for_timeout(1500)

                        # --- Click "Track Another Shipment" ---
                        logger.info("Waiting for 'Track Another Shipment' button...")
                        track_another_btn = None
                        for _ in range(35):
                            btns = page.query_selector_all("button, input[type='button'], a[role='button']")
                            for btn in btns:
                                try:
                                    text = btn.inner_text().strip().lower()
                                    if "track another shipment" in text and btn.is_visible() and btn.is_enabled():
                                        track_another_btn = btn
                                        break
                                except Exception:
                                    continue
                            if track_another_btn and track_another_btn.is_visible() and track_another_btn.is_enabled():
                                track_another_btn.scroll_into_view_if_needed()
                                track_another_btn.hover()
                                self._human_like_delay()
                                track_another_btn.click()
                                logger.info("Clicked 'Track Another Shipment' button.")
                                self._human_like_delay()
                                page.wait_for_timeout(1500)
                                break
                            page.wait_for_timeout(1000)
                        if not (track_another_btn and track_another_btn.is_visible()):
                            logger.error("Could not find or click 'Track Another Shipment' button!")
                            page.screenshot(path="fedex_track_another_not_found.png")
                            raise Exception("'Track Another Shipment' button not found or not interactable.")

                        # --- Find ANY visible text input in the central form (ignore id/class) ---
                        logger.info("Waiting for tracking input after 'Track Another Shipment'...")
                        input_box = None
                        for _ in range(40):
                            input_candidates = page.query_selector_all("input[type='text']")
                            for inp in input_candidates:
                                try:
                                    if inp.is_visible() and inp.is_enabled():
                                        # Only use if input is not in the top nav bar (use bounding box)
                                        box = inp.bounding_box()
                                        if box and box['y'] > 150:
                                            input_box = inp
                                            break
                                except Exception:
                                    continue
                            if input_box:
                                input_box.scroll_into_view_if_needed()
                                input_box.click()
                                self._human_like_delay()
                                input_box.fill("")
                                input_box.type(self.tracking_number, delay=random.randint(70, 120))
                                logger.info(f"Typed tracking number: {self.tracking_number}")
                                self._human_like_delay()
                                page.wait_for_timeout(900)
                                break
                            page.wait_for_timeout(700)
                        if not input_box:
                            logger.error("Tracking input not found after 'Track Another Shipment'!")
                            page.screenshot(path="fedex_input_any_text_not_found.png")
                            raise Exception("Tracking input not found after 'Track Another Shipment'.")

                        # --- Find any visible/enabled button with "track" text/value ---
                        logger.info("Looking for TRACK button in the form...")
                        track_btn = None
                        for _ in range(25):
                            buttons = page.query_selector_all("button, input[type='submit']")
                            for btn in buttons:
                                try:
                                    if btn.is_visible() and btn.is_enabled():
                                        text = btn.inner_text().strip().lower() if hasattr(btn, "inner_text") else ""
                                        value = btn.get_attribute("value") or ""
                                        if ("track" in text or "track" in value) and len(text) < 15:
                                            btn_box = btn.bounding_box()
                                            if btn_box and btn_box['y'] > 200:
                                                track_btn = btn
                                                break
                                except Exception:
                                    continue
                            if track_btn:
                                track_btn.scroll_into_view_if_needed()
                                self._human_like_delay()
                                track_btn.click()
                                logger.info("Clicked TRACK button in form.")
                                self._human_like_delay()
                                break
                            page.wait_for_timeout(600)
                        if not track_btn:
                            logger.error("TRACK button not found after input!")
                            page.screenshot(path="fedex_any_track_btn_not_found.png")
                            raise Exception("TRACK button not found after input.")

                        # --- Wait for tracking results page ---
                        logger.info("Waiting for tracking results page...")
                        page.wait_for_selector(
                            ".shipment-status-progress-container, .milestone-container, .tracking-results, #trackingResults_heading",
                            timeout=90000
                        )
                        page.wait_for_timeout(2500)
                        html_content = page.content()
                        return self._parse_tracking_info(html_content)

                    except Exception as e:
                        logger.error(f"Attempt {self.current_retry + 1} failed: {str(e)}")
                        self.current_retry += 1
                        self.user_agent = self.ua.random
                        continue
                    finally:
                        context.close()
                        browser.close()

            except Exception as e:
                logger.error(f"Fatal error: {str(e)}")
                return self._error_response(str(e))

        return self._error_response("Max retries exceeded")

    def _parse_tracking_info(self, html_content: str) -> TrackingResponse:
        from datetime import datetime

        def clean(x):
            if not x:
                return ""
            return " ".join(x.split()).replace("\xa0", " ").strip()

        soup = BeautifulSoup(html_content, "html.parser")
        events = []

        # Try to parse the travel history table (the real FedEx timeline)
        table = soup.select_one("table.fdx-c-table, table[role='presentation']")
        if table:
            rows = table.find_all("tr")
            for tr in rows:
                tds = tr.find_all("td")
                if len(tds) >= 3:
                    # Format: [Date, Time, Event, Location]
                    date_col = clean(tds[0].get_text())
                    time_col = clean(tds[1].get_text())
                    event_col = clean(tds[2].get_text())
                    location_col = clean(tds[3].get_text()) if len(tds) > 3 else ""
                    # Build a clean datetime
                    datetime_val = ""
                    try:
                        # Handles "Friday, 4/25/25" or just "4/25/25"
                        if "," in date_col:
                            _, date_val = date_col.split(",", 1)
                            date_val = date_val.strip()
                        else:
                            date_val = date_col
                        dt = datetime.strptime(date_val, "%m/%d/%y")
                        date_fmt = dt.strftime("%B %d, %Y")
                    except Exception:
                        date_fmt = date_col
                    if date_fmt and time_col:
                        datetime_val = f"{date_fmt}, {time_col}"
                    elif date_fmt:
                        datetime_val = date_fmt
                    else:
                        datetime_val = time_col
                    events.append(TrackingEvent(
                        event=event_col,
                        location=location_col,
                        datetime=datetime_val,
                        note=None
                    ))

        # Fallback: simple timeline if table not found
        if not events:
            for step in soup.select(".shipment-status-progress-container .shipment-status-progress-step"):
                event_label = step.select_one(".shipment-status-progress-step-label")
                event_label_text = clean(event_label.get_text()) if event_label else ""
                event_content = step.select_one(".shipment-status-progress-step-content")
                location = ""
                datetime_val = ""
                if event_content:
                    event_parts = [clean(x) for x in event_content.stripped_strings]
                    if len(event_parts) == 2:
                        location, datetime_val = event_parts
                    elif len(event_parts) == 1:
                        if "/" in event_parts[0] or ":" in event_parts[0]:
                            datetime_val = event_parts[0]
                        else:
                            location = event_parts[0]
                events.append(TrackingEvent(
                    event=event_label_text,
                    location=location,
                    datetime=datetime_val,
                    note=None
                ))

        # Shipment status detection (never use "From" or "To")
        KNOWN_STATUSES = [
            "Delivered",
            "Exception",
            "Out for delivery",
            "In transit",
            "On the way",
            "Picked up",
            "Pending",
            "Shipment information sent to FedEx",
            "Shipment exception",
            "Returning to sender",
            "Arrived at FedEx location",
            "Left FedEx origin facility",
            "Available for pickup"
        ]

        status = "Unknown"
        delivered_at = ""
        delivery_location = ""

        # Set by first matching known status, in priority order
        for known_status in KNOWN_STATUSES:
            for ev in events:
                if ev.event and known_status.lower() in ev.event.lower():
                    status = known_status
                    if "delivered" in known_status.lower():
                        delivered_at = ev.datetime
                        delivery_location = ev.location
                    break
            if status == known_status:
                break

        # Fallbacks if no status matched
        if status == "Unknown" and events:
            # Use last event's info if nothing matches
            status = events[-1].event
            delivered_at = events[-1].datetime
            delivery_location = events[-1].location

        # Final fallback: if "delivered_at" still empty, use last event's datetime/location
        if not delivered_at and events:
            delivered_at = events[-1].datetime
        if not delivery_location and events:
            delivery_location = events[-1].location

        return TrackingResponse(
            tracking=self.tracking_number,
            carrier="FedEx",
            shipment_status=status or "Unknown",
            delivered_at=delivered_at,
            delivery_location=delivery_location,
            route_summary=events
        )


