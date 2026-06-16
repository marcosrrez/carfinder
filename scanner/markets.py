# scanner/markets.py
"""ZIP-to-Craigslist market resolver.

Uses pgeocode for ZIP→lat/lon (bundled USPS data, no API key needed).
Haversine distance determines which Craigslist metros fall within the
search radius.
"""
import math
import pgeocode

# (city_label, subdomain, lat, lon)
CRAIGSLIST_MARKETS = [
    ("New York",         "newyork",       40.713,  -74.006),
    ("Los Angeles",      "losangeles",    34.052, -118.244),
    ("Chicago",          "chicago",       41.878,  -87.630),
    ("Houston",          "houston",       29.760,  -95.370),
    ("Phoenix",          "phoenix",       33.449, -112.074),
    ("Philadelphia",     "philadelphia",  39.952,  -75.165),
    ("San Antonio",      "sanantonio",    29.425,  -98.494),
    ("San Diego",        "sandiego",      32.716, -117.163),
    ("Dallas",           "dallas",        32.783,  -96.800),
    ("San Jose",         "sfbay",         37.338, -121.886),
    ("Austin",           "austin",        30.267,  -97.743),
    ("Jacksonville",     "jacksonville",  30.332,  -81.656),
    ("Columbus OH",      "columbus",      39.961,  -82.999),
    ("Charlotte",        "charlotte",     35.227,  -80.843),
    ("Indianapolis",     "indianapolis",  39.768,  -86.158),
    ("San Francisco",    "sfbay",         37.774, -122.419),
    ("Seattle",          "seattle",       47.606, -122.332),
    ("Denver",           "denver",        39.739, -104.984),
    ("Nashville",        "nashville",     36.162,  -86.781),
    ("Oklahoma City",    "oklahoma",      35.467,  -97.516),
    ("El Paso",          "elpaso",        31.758, -106.487),
    ("Washington DC",    "washingtondc",  38.907,  -77.037),
    ("Las Vegas",        "lasvegas",      36.175, -115.136),
    ("Louisville",       "louisville",    38.252,  -85.758),
    ("Baltimore",        "baltimore",     39.290,  -76.612),
    ("Milwaukee",        "milwaukee",     43.039,  -87.906),
    ("Albuquerque",      "albuquerque",   35.085, -106.651),
    ("Tucson",           "tucson",        32.222, -110.971),
    ("Fresno",           "fresno",        36.748, -119.772),
    ("Sacramento",       "sacramento",    38.582, -121.494),
    ("Kansas City",      "kansascity",    39.099,  -94.578),
    ("Atlanta",          "atlanta",       33.749,  -84.388),
    ("Omaha",            "omaha",         41.257,  -95.938),
    ("Colorado Springs", "cosprings",     38.834, -104.821),
    ("Raleigh",          "raleigh",       35.772,  -78.639),
    ("Minneapolis",      "minneapolis",   44.977,  -93.265),
    ("Tampa",            "tampa",         27.948,  -82.458),
    ("New Orleans",      "neworleans",    29.951,  -90.072),
    ("Cleveland",        "cleveland",     41.499,  -81.695),
    ("Pittsburgh",       "pittsburgh",    40.440,  -79.996),
    ("Portland OR",      "portland",      45.523, -122.676),
    ("Cincinnati",       "cincinnati",    39.103,  -84.512),
    ("St. Louis",        "stlouis",       38.627,  -90.198),
    ("Detroit",          "detroit",       42.331,  -83.046),
    ("Memphis",          "memphis",       35.149,  -90.052),
    ("Boston",           "boston",        42.360,  -71.058),
    ("Miami",            "miami",         25.774,  -80.194),
    ("Orlando",          "orlando",       28.538,  -81.379),
    ("Salt Lake City",   "saltlakecity",  40.760, -111.891),
    ("Richmond VA",      "richmond",      37.541,  -77.434),
    ("Hartford",         "hartford",      41.763,  -72.685),
    ("Buffalo",          "buffalo",       42.887,  -78.879),
    ("Birmingham AL",    "birmingham",    33.520,  -86.802),
    ("Rochester NY",     "rochester",     43.157,  -77.615),
    ("Fayetteville AR",  "fayar",         36.062,  -94.157),
    ("Tulsa",            "tulsa",         36.154,  -95.993),
    ("Little Rock",      "littlerock",    34.746,  -92.290),
    ("Springfield MO",   "springfield",   37.215,  -93.292),
    ("Wichita",          "wichita",       37.692,  -97.337),
    ("Knoxville",        "knoxville",     35.961,  -83.921),
    ("Baton Rouge",      "batonrouge",    30.451,  -91.154),
    ("Greensboro NC",    "greensboro",    36.073,  -79.792),
    ("Greenville SC",    "greenville",    34.852,  -82.394),
    ("Lexington KY",     "lexington",     38.040,  -84.458),
    ("Spokane",          "spokane",       47.659, -117.426),
    ("Boise",            "boise",         43.615, -116.202),
]

_nomi = None

def _get_nomi():
    global _nomi
    if _nomi is None:
        _nomi = pgeocode.Nominatim("us")
    return _nomi


def zip_to_coords(zip_code: str) -> tuple[float, float] | None:
    """Return (lat, lon) for a US ZIP code, or None if not found."""
    try:
        nomi = _get_nomi()
        result = nomi.query_postal_code(zip_code.strip())
        lat = result.get("latitude")
        lon = result.get("longitude")
        if lat is None or lon is None or math.isnan(float(lat)) or math.isnan(float(lon)):
            return None
        return float(lat), float(lon)
    except Exception:
        return None


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles between two lat/lon points."""
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def craigslist_markets_near(zip_code: str, radius_miles: int) -> list[tuple[str, str]]:
    """Return list of (city_label, subdomain) for Craigslist markets within radius_miles of zip_code.

    Returns empty list if ZIP cannot be resolved.
    Deduplicates by subdomain (multiple cities may share one CL site).
    """
    coords = zip_to_coords(zip_code)
    if coords is None:
        return []
    lat, lon = coords
    seen_subdomains: set[str] = set()
    results: list[tuple[str, str]] = []
    for city_label, subdomain, mkt_lat, mkt_lon in CRAIGSLIST_MARKETS:
        if subdomain in seen_subdomains:
            continue
        dist = _haversine_miles(lat, lon, mkt_lat, mkt_lon)
        if dist <= radius_miles:
            results.append((city_label, subdomain))
            seen_subdomains.add(subdomain)
    return results
