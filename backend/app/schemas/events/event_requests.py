from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Optional


class IncomingEventSchema(BaseModel):
    title: str
    description: str
    location: str
    date: datetime
    status: Literal["active", "cancelled"]
    fee: int
    support_contact: str
    after_booking_message: str

class IncomingEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    date: Optional[datetime] = None
    status: Optional[Literal["active", "cancelled"]] = None
    fee: Optional[int] = None
    support_contact: Optional[str] = None
    after_booking_message: Optional[str] = None
