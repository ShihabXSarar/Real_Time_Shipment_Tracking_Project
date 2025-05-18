from pydantic import BaseModel, Field
from typing import List, Optional


class TrackingEvent(BaseModel):
    """Model for a single tracking event in the shipment's journey"""
    event: str
    location: str
    datetime: Optional[str] = None
    note: Optional[str] = None


class TrackingResponse(BaseModel):
    """Model for the standardized tracking response"""
    tracking: str
    carrier: str
    shipment_status: str
    delivered_at: Optional[str] = None
    delivery_location: Optional[str] = None
    route_summary: List[TrackingEvent] = Field(default_factory=list)