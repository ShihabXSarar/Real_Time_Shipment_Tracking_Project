from abc import ABC, abstractmethod
from ..schemas.tracking import TrackingResponse


class BaseScraper(ABC):
    """Base class for all carrier-specific scrapers"""

    def __init__(self, tracking_number: str):
        self.tracking_number = tracking_number

    @abstractmethod
    def scrape(self) -> TrackingResponse:
        """
        Scrape the carrier's website for tracking information

        Returns:
            TrackingResponse: Standardized tracking information
        """
        pass

    def _error_response(self, error_msg: str) -> TrackingResponse:
        """
        Create an error response when scraping fails

        Args:
            error_msg: The error message

        Returns:
            TrackingResponse: Error response with minimal information
        """
        return TrackingResponse(
            tracking=self.tracking_number,
            carrier=self.__class__.__name__.replace("Scraper", ""),
            shipment_status=f"Error: {error_msg}",
            delivered_at=None,
            delivery_location=None,
            route_summary=[]
        )