"""
Distance calculation for nearest-hospital matching. Uses the Haversine formula — accurate
enough for "which hospital is closest" ranking at city/regional scale, and needs no extra
infrastructure (PostGIS was deliberately deferred back on Day 1's settings.py to keep local
setup simple; this covers the actual need without that dependency).

If the hospital count ever grows large enough that computing distance in Python for every
request becomes slow, the natural upgrade path is PostGIS + a spatial index — the Day 1
settings.py comment already flags exactly where to make that swap.
"""
import math


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two lat/lng points, in kilometers."""
    R = 6371.0  # Earth's radius in km

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
