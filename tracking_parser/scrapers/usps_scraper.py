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

class USPSScraper(BaseScraper):
    def __init__(self, tracking_number: str):
        super().__init__(tracking_number)
        self.ua = UserAgent()
        self.user_agent = self.ua.random
        self.max_retries = 3
        self.current_retry = 0
        self.tracking_url = "https://tools.usps.com/go/TrackConfirmAction"

    def _human_like_delay(self):
        base_delay = random.uniform(1.0, 2.5)
        delay = base_delay * (1.5 ** self.current_retry)
        logger.info(f"Human-like delay: {delay:.2f}s")
        time.sleep(delay)

    def _stealth_setup(self, page):
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {}, loadTimes: () => {} };
            delete navigator.__proto__.webdriver;
        """)

    def scrape(self) -> TrackingResponse:
        while self.current_retry < self.max_retries:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,  # debug: set True in production
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--disable-infobars",
                            "--no-sandbox",
                            "--window-size=1920,1080"
                        ],
                        slow_mo=random.randint(50, 200)
                    )

                    context = browser.new_context(
                        user_agent=self.user_agent,
                        viewport={"width": 1920, "height": 1080},
                        locale="en-US",
                        bypass_csp=True
                    )

                    try:
                        page = context.new_page()
                        self._stealth_setup(page)

                        logger.info(f"Navigating to USPS tracking: {self.tracking_url}")
                        page.goto(self.tracking_url, wait_until="networkidle", timeout=60000)
                        self._human_like_delay()

                        # Accept cookies if present
                        try:
                            page.click("#agree-button, button:has-text('Accept')", timeout=5000)
                            logger.info("Accepted cookies")
                            self._human_like_delay()
                        except Exception:
                            pass

                        # Fill tracking number in the form
                        input_box = page.wait_for_selector("#tracking-input, input[data-testid='tracking-input']", timeout=20000)
                        input_box.click()
                        for char in self.tracking_number:
                            input_box.type(char, delay=random.uniform(40, 120))
                        self._human_like_delay()

                        # Click the "Track" button
                        track_button = page.wait_for_selector("button#track-package-button, button[data-testid='track-button'], button:has-text('Track')", timeout=10000)
                        track_button.click()
                        self._human_like_delay()

                        # Wait for tracking results to load
                        page.wait_for_selector(
                            ".tracking-progress-bar-status-container, [data-testid='tracking-results'], #trackingResults_heading",
                            timeout=90000
                        )

                        html_content = page.content()
                        # Save for debugging if needed:
                        with open("debug_usps_page.html", "w", encoding="utf-8") as f:
                            f.write(html_content)
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
                return self._error_response(str(e))

        return self._error_response("Max retries exceeded")

    def _parse_tracking_info(self, html_content: str) -> TrackingResponse:
        def clean_text(x):
            if not x:
                return ""
            return " ".join(x.split()).strip()

        soup = BeautifulSoup(html_content, "html.parser")

        # Shipment Status: get the .tb-status from the FIRST .tb-step.current-step
        status = None
        first_step = soup.select_one(".tracking-progress-bar-status-container .tb-step.current-step")
        if first_step:
            status_elem = first_step.select_one(".tb-status")
            status = clean_text(status_elem.get_text()) if status_elem else None
            if not status:
                status_detail_elem = first_step.select_one(".tb-status-detail")
                status = clean_text(status_detail_elem.get_text()) if status_detail_elem else "Unknown"
        else:
            status = "Unknown"

        events = []
        for step in soup.select(".tracking-progress-bar-status-container .tb-step"):
            detail = step.select_one(".tb-status-detail")
            location = step.select_one(".tb-location")
            date = step.select_one(".tb-date")
            event = clean_text(detail.get_text()) if detail else ""
            location_text = clean_text(location.get_text()) if location else ""
            date_text = clean_text(date.get_text()) if date else ""
            note = None
            if event or date_text:
                events.append(TrackingEvent(
                    event=event,
                    location=location_text,
                    datetime=date_text,
                    note=note
                ))

        delivered_at = None
        delivery_location = None
        if any('delivered' in (e.event or '').lower() for e in events):
            for e in events:
                if 'delivered' in (e.event or '').lower():
                    delivered_at = e.datetime
                    delivery_location = e.location
                    break

        return TrackingResponse(
            tracking=self.tracking_number,
            carrier="USPS",
            shipment_status=status,
            delivered_at=delivered_at,
            delivery_location=delivery_location,
            route_summary=events
        )


