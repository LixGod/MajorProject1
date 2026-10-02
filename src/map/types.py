from pydantic import BaseModel
from typing import Optional, List

class JunctionLocation(BaseModel):
    junction_id: str
    name: str
    latitude: float
    longitude: float
    address: str
    source: str  # "tomtom" or "fallback_cache"
    city: str = "Mumbai"
