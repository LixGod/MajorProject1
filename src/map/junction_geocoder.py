from typing import Dict, Any, Optional
from src.map.tomtom_client import TomTomMapsClient
from src.map.types import JunctionLocation

# Fallback coordinates for key Mumbai junctions if TomTom API is offline or key missing
MUMBAI_FALLBACK_JUNCTIONS: Dict[str, Dict[str, Any]] = {
    "weh_vile_parle": {
        "name": "WEH Vile Parle Junction",
        "latitude": 19.0968,
        "longitude": 72.8517,
        "address": "Western Express Highway, Vile Parle East, Mumbai, Maharashtra 400057"
    },
    "bkc_connector": {
        "name": "Bandra Kurla Complex Junction",
        "latitude": 19.0657,
        "longitude": 72.8686,
        "address": "BKC Connector, Bandra East, Mumbai, Maharashtra 400051"
    },
    "dadar_tt_circle": {
        "name": "Dadar TT Circle",
        "latitude": 19.0178,
        "longitude": 72.8478,
        "address": "Dadar TT Circle, Dadar East, Mumbai, Maharashtra 400014"
    },
    "andheri_flyover": {
        "name": "Andheri SV Road Junction",
        "latitude": 19.1197,
        "longitude": 72.8464,
        "address": "SV Road, Andheri West, Mumbai, Maharashtra 400058"
    },
    "powai_galleria": {
        "name": "Powai Hiranandani Junction",
        "latitude": 19.1176,
        "longitude": 72.9060,
        "address": "Central Ave, Powai, Mumbai, Maharashtra 400076"
    }
}

class JunctionGeocoder:
    """
    High-level Geocoder abstraction combining live TomTom Maps API lookup
    with robust Mumbai fallback cache.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.tomtom_client = TomTomMapsClient(api_key=api_key)

    def resolve_junction_location(
        self,
        junction_id: str,
        junction_name: str,
        configured_lat: Optional[float] = None,
        configured_lon: Optional[float] = None,
        configured_address: Optional[str] = None
    ) -> JunctionLocation:
        # 1. Try live TomTom geocoding if available
        if self.tomtom_client.is_available():
            geo_res = self.tomtom_client.geocode_location(junction_name)
            if geo_res:
                return JunctionLocation(
                    junction_id=junction_id,
                    name=junction_name,
                    latitude=geo_res["latitude"],
                    longitude=geo_res["longitude"],
                    address=geo_res["address"],
                    source="tomtom"
                )

        # 2. Use manual configured lat/lon if provided
        if configured_lat is not None and configured_lon is not None:
            return JunctionLocation(
                junction_id=junction_id,
                name=junction_name,
                latitude=configured_lat,
                longitude=configured_lon,
                address=configured_address or junction_name,
                source="configured"
            )

        # 3. Fallback to Mumbai predefined junction database
        fallback = MUMBAI_FALLBACK_JUNCTIONS.get(
            junction_id,
            MUMBAI_FALLBACK_JUNCTIONS.get("weh_vile_parle")
        )
        return JunctionLocation(
            junction_id=junction_id,
            name=junction_name or fallback["name"],
            latitude=fallback["latitude"],
            longitude=fallback["longitude"],
            address=fallback["address"],
            source="fallback_cache"
        )
