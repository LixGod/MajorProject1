import os
from typing import Optional, Dict, Any
import requests

class TomTomMapsClient:
    """
    TomTom Maps API client for geocoding junction locations.
    Reads TOMTOM_API_KEY from environment.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TOMTOM_API_KEY")
        self.base_url = "https://api.tomtom.com/search/2/geocode"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    def geocode_location(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Geocodes a junction address or landmark query in Mumbai.
        Returns dict with lat, lon, address.
        """
        if not self.is_available():
            print("[TomTomClient WARNING] TOMTOM_API_KEY not configured. Skipping live TomTom lookup.")
            return None

        try:
            full_query = f"{query}, Mumbai, Maharashtra, India"
            url = f"{self.base_url}/{requests.utils.quote(full_query)}.json"
            params = {
                "key": self.api_key,
                "limit": 1,
                "countrySet": "IN"
            }
            resp = requests.get(url, params=params, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    res = results[0]
                    pos = res.get("position", {})
                    addr = res.get("address", {}).get("freeformAddress", query)
                    return {
                        "latitude": float(pos.get("lat", 19.0760)),
                        "longitude": float(pos.get("lon", 72.8777)),
                        "address": addr,
                        "source": "tomtom"
                    }
        except Exception as e:
            print(f"[TomTomClient ERROR] Geocoding request failed: {e}")

        return None
