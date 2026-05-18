"""Per-UAT nearest-service Euclidean distance, projected CRS."""
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from pipeline.config import INTERMEDIATE_DIR, ROMANIA_STEREO_70, WGS84


def nearest_distance_m(origin: Point, services: gpd.GeoDataFrame):
    if services is None or services.empty:
        return float("nan"), ""
    dists = services.geometry.distance(origin)
    idx = dists.idxmin()  # label, not position; use .loc to honour gaps from upstream dropna.
    return float(dists.loc[idx]), str(services.loc[idx, "id"])


def load_services(name: str) -> gpd.GeoDataFrame | None:
    path = INTERMEDIATE_DIR / f"{name}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path).dropna(subset=["lat", "lng"]).reset_index(drop=True)
    if df.empty:
        return None
    df["id"] = df.index.astype(str)
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lng, df.lat), crs=WGS84).to_crs(ROMANIA_STEREO_70)


def main():
    uats = gpd.read_file(INTERMEDIATE_DIR / "uats_timis.geojson").to_crs(ROMANIA_STEREO_70)
    uats["centroid"] = uats.geometry.centroid
    schools = load_services("schools")
    gps = load_services("gps_geocoded")
    hospitals = load_services("hospitals")
    rows = []
    for _, row in uats.iterrows():
        c = row["centroid"]
        d_school, _ = nearest_distance_m(c, schools)
        d_gp, _ = nearest_distance_m(c, gps)
        d_er, _ = nearest_distance_m(c, hospitals)
        rows.append({
            "siruta": str(row.get("siruta") or row.get("siruta_uat") or ""),
            "name": row.get("name") or row.get("nume") or row.get("denumire"),
            "nearest_school_m": d_school,
            "nearest_gp_m": d_gp,
            "nearest_er_m": d_er,
        })
    pd.DataFrame(rows).to_csv(INTERMEDIATE_DIR / "uat_distances.csv", index=False)
    print(f"Wrote {len(rows)} UAT distances "
          f"(schools={'ok' if schools is not None else 'MISSING'}, "
          f"gps={'ok' if gps is not None else 'MISSING'}, "
          f"er={'ok' if hospitals is not None else 'MISSING'})")


if __name__ == "__main__":
    main()
