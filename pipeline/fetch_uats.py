"""Fetch Timiș UAT polygons from OpenStreetMap via Overpass API.

ANCPI ArcGIS REST is the canonical source but was 500/502 on 2026-05-18.
OSM admin_level=8 in RO-TM yields the same ~99 UATs. Migrate back to
ANCPI for v1.
"""
import json
import requests
import osm2geojson
from pipeline.config import INTERMEDIATE_DIR, RAW_DIR

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_QUERY = """
[out:json][timeout:90];
area["ISO3166-2"="RO-TM"]->.tm;
relation(area.tm)[boundary=administrative][admin_level=8];
out geom;
"""
USER_AGENT = "desertul-banat civic-data (vladtemian@gmail.com)"


def fetch_overpass() -> dict:
    r = requests.post(OVERPASS_URL, data={"data": OVERPASS_QUERY},
                      headers={"User-Agent": USER_AGENT}, timeout=180)
    r.raise_for_status()
    try:
        return r.json()
    except ValueError as e:
        # Overpass under load returns 200 OK with HTML "runtime error" bodies.
        raise RuntimeError(f"Overpass returned non-JSON (likely overloaded). First 500 chars:\n{r.text[:500]}") from e


def normalize_features(fc: dict) -> dict:
    kept = []
    for f in fc["features"]:
        tags = f["properties"].get("tags", {})
        kept.append({
            "type": "Feature",
            "geometry": f["geometry"],
            "properties": {
                "name": tags.get("name") or tags.get("official_name") or "",
                "judet": "TIMIȘ",
                "admin_level": tags.get("admin_level"),
                "wikidata": tags.get("wikidata"),
                "place": tags.get("place"),
                "osm_id": f["properties"].get("id"),
            },
        })
    return {"type": "FeatureCollection", "features": kept}


def main():
    raw_path = RAW_DIR / "osm_overpass_timis.json"
    if raw_path.exists():
        osm = json.loads(raw_path.read_text())
    else:
        osm = fetch_overpass()
        raw_path.write_text(json.dumps(osm))
    fc_raw = osm2geojson.json2geojson(osm)
    fc = normalize_features(fc_raw)
    if not 95 <= len(fc["features"]) <= 105:
        raise RuntimeError(f"Expected ~99 UATs, got {len(fc['features'])}")
    out = INTERMEDIATE_DIR / "uats_timis.geojson"
    out.write_text(json.dumps(fc))
    print(f"Wrote {len(fc['features'])} UATs to {out}")


if __name__ == "__main__":
    main()
