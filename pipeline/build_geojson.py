"""Merge UAT polygons + scores + precomputed colors (Cosette pattern)."""
import math
import geopandas as gpd
import pandas as pd
from pipeline.config import INTERMEDIATE_DIR, WEB_DATA_DIR
from pipeline.uat_match import build_timis_name_to_siruta, lookup_siruta

RAMP = [(0,"#3b0a0a"),(20,"#7a1a1a"),(40,"#b54545"),(60,"#d99080"),(80,"#e8c8b8"),(100,"#f5ecd9")]
MISSING_COLOR = "#9a9a9a"

def color_for(score: float) -> str:
    if score is None or (isinstance(score, float) and math.isnan(score)):
        return MISSING_COLOR
    for threshold, color in RAMP:
        if score <= threshold: return color
    return RAMP[-1][1]

def main():
    uats = gpd.read_file(INTERMEDIATE_DIR / "uats_timis.geojson")
    scores = pd.read_csv(INTERMEDIATE_DIR / "uat_scores.csv")
    name_to_siruta = build_timis_name_to_siruta()
    uats["siruta"] = uats["name"].apply(lambda n: lookup_siruta(n, name_to_siruta) or "")
    unmatched = uats["siruta"].eq("").sum()
    if unmatched > 5:
        raise RuntimeError(f"{unmatched} OSM UATs without SIRUTA match; investigate name-normalisation rules")
    merged = uats.merge(scores, on="name", how="left", suffixes=("", "_score"))
    for view in ("composite", "school", "gp", "hospital"):
        merged[f"_color_{view}"] = merged[f"{view}_score"].apply(color_for)
    merged["_display_color"] = merged["_color_composite"]
    merged["partial_data"] = merged["partial_data"].fillna(True)
    out = WEB_DATA_DIR / "uats_timis.geojson"
    out.write_text(merged.to_json())
    print(f"Wrote {len(merged)} UATs to {out} ({unmatched} without SIRUTA match)")

if __name__ == "__main__":
    main()
