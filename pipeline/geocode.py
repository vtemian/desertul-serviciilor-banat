import json
import time
import requests
from pipeline.config import DATA_DIR

CACHE_PATH = DATA_DIR / "cache" / "nominatim.json"
CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
USER_AGENT = "desertul-serviciilor-banat/0.1 (vladtemian@gmail.com)"
LAST_CALL_AT = [0.0]

def _load_cache() -> dict:
    return json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}

def _save_cache(cache: dict) -> None:
    CACHE_PATH.write_text(json.dumps(cache))

def geocode_address(query: str):
    cache = _load_cache()
    if query in cache:
        return tuple(cache[query]) if cache[query] else (None, None)
    elapsed = time.monotonic() - LAST_CALL_AT[0]
    if elapsed < 1.05:
        time.sleep(1.05 - elapsed)
    r = requests.get("https://nominatim.openstreetmap.org/search",
                     params={"q": query, "format": "json", "limit": 1, "countrycodes": "ro"},
                     headers={"User-Agent": USER_AGENT}, timeout=20)
    LAST_CALL_AT[0] = time.monotonic()
    r.raise_for_status()
    hits = r.json()
    if not hits:
        cache[query] = None
        _save_cache(cache)
        return None, None
    lat, lng = float(hits[0]["lat"]), float(hits[0]["lon"])
    cache[query] = [lat, lng]
    _save_cache(cache)
    return lat, lng
