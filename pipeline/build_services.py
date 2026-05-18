"""Build services_timis.geojson — schools, GPs (when available), hospitals."""
import json
import pandas as pd
from pipeline.config import INTERMEDIATE_DIR, WEB_DATA_DIR


def points_for(name: str, type_: str, fields: dict) -> list:
    path = INTERMEDIATE_DIR / f"{name}.csv"
    if not path.exists():
        return []
    df = pd.read_csv(path).dropna(subset=["lat", "lng"])
    feats = []
    for _, r in df.iterrows():
        props = {"type": type_}
        for dest, src in fields.items():
            props[dest] = r.get(src)
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(r["lng"]), float(r["lat"])]},
            "properties": props,
        })
    return feats


def main():
    features = []
    features += points_for("schools", "school", {"name": "name", "locality": "localitate", "uat": "uat_name"})
    features += points_for("gps_geocoded", "gp", {"name": "name", "address": "address", "locality": "locality"})  # may be absent until B6/B7
    features += points_for("hospitals", "hospital", {"name": "name", "uat": "uat_name"})
    out = WEB_DATA_DIR / "services_timis.geojson"
    out.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    counts = {t: sum(1 for f in features if f["properties"]["type"] == t) for t in ("school", "gp", "hospital")}
    print(f"Wrote {len(features)} service points ({counts}) to {out}")


if __name__ == "__main__":
    main()
