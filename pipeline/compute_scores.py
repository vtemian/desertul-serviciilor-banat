"""Per-UAT scores and composite (0.4 school + 0.4 GP + 0.2 hospital)."""
from __future__ import annotations
import math
import geopandas as gpd
import pandas as pd
from pipeline.config import INTERMEDIATE_DIR, SCORE_WEIGHTS, ROMANIA_STEREO_70, WGS84


def _is_nan(x):
    return x is None or (isinstance(x, float) and math.isnan(x))


def school_score(nearest_m: float) -> float:
    """100 at <= 1 km, 0 at >= 8 km."""
    if _is_nan(nearest_m):
        return float("nan")
    km = nearest_m / 1000
    return max(0.0, min(100.0, 100 * (8 - km) / 7))


def gp_score(pop_total: int, gp_count: int | None) -> float:
    """100 at <= 1500 residents per GP, 0 at >= 4000.

    gp_count=None means data missing (returns NaN, composite renormalizes).
    gp_count=0 means data confirms zero GPs in the UAT (score 0, real signal).
    """
    if pop_total is None or pop_total < 1:
        return float("nan")
    if gp_count is None:
        return float("nan")
    if gp_count <= 0:
        return 0.0
    ratio = pop_total / gp_count
    return max(0.0, min(100.0, 100 * (4000 - ratio) / 2500))


def hospital_score(nearest_m: float) -> float:
    """100 at <= 10 km, 0 at >= 50 km (straight-line proxy for ~15 min drive)."""
    if _is_nan(nearest_m):
        return float("nan")
    km = nearest_m / 1000
    return max(0.0, min(100.0, 100 * (50 - km) / 40))


def composite(school: float, gp: float, hospital: float) -> float:
    parts = [(SCORE_WEIGHTS[k], v) for k, v in (("school", school), ("gp", gp), ("hospital", hospital)) if not _is_nan(v)]
    if not parts:
        return float("nan")
    total_w = sum(w for w, _ in parts)
    return sum(w * v for w, v in parts) / total_w


def gps_per_uat() -> pd.Series:
    """GP count per UAT siruta. Returns empty Series if gps_geocoded.csv missing (B6/B7 deferred)."""
    path = INTERMEDIATE_DIR / "gps_geocoded.csv"
    if not path.exists():
        return pd.Series(dtype=int)
    gps = pd.read_csv(path).dropna(subset=["lat", "lng"])
    g_gps = gpd.GeoDataFrame(gps, geometry=gpd.points_from_xy(gps.lng, gps.lat), crs=WGS84)
    uats = gpd.read_file(INTERMEDIATE_DIR / "uats_timis.geojson")[["siruta", "geometry"]]
    return gpd.sjoin(g_gps, uats, predicate="within", how="left").groupby("siruta").size()


def population_per_uat() -> pd.Series:
    pop = pd.read_csv(INTERMEDIATE_DIR / "population.csv", dtype={"siruta": str})
    pop["uat_siruta"] = pop["siruta"].str[:6]
    return pop.groupby("uat_siruta")["pop_total"].sum()


def main():
    distances = pd.read_csv(INTERMEDIATE_DIR / "uat_distances.csv", dtype={"siruta": str})
    gp_counts = gps_per_uat()
    gp_data_present = not gp_counts.empty
    populations = population_per_uat()
    rows = []
    for _, r in distances.iterrows():
        siruta = r["siruta"]
        pop = int(populations.get(siruta, 0))
        gp_cnt = int(gp_counts.get(siruta, 0)) if gp_data_present else None
        s = school_score(r["nearest_school_m"])
        g = gp_score(pop, gp_cnt)
        h = hospital_score(r["nearest_er_m"])
        c = composite(s, g, h)
        rows.append({
            "siruta": siruta, "name": r["name"], "pop_total": pop,
            "gp_count": gp_cnt if gp_cnt is not None else "",
            "nearest_school_m": r["nearest_school_m"], "nearest_gp_m": r["nearest_gp_m"], "nearest_er_m": r["nearest_er_m"],
            "school_score": s, "gp_score": g, "hospital_score": h, "composite_score": c,
            "partial_data": any(map(_is_nan, [s, g, h])),
        })
    pd.DataFrame(rows).to_csv(INTERMEDIATE_DIR / "uat_scores.csv", index=False)
    print(f"Wrote {len(rows)} UAT scores (gp_data_present={gp_data_present})")


if __name__ == "__main__":
    main()
