"""Fetch 2016-2017 SIIIR Timiș schools with pre-geocoded coordinates.

retea2016-2017.csv (UTF-16 LE TSV) carries the registry; coordonategps-scoli.xlsx
carries lat/lng keyed by Cod SIIIR. We auto-join, filter to TM "Unitate de
învățământ", drop closed units, and emit a single schools.csv.
"""
import requests
import pandas as pd
from pipeline.config import RAW_DIR, INTERMEDIATE_DIR

RETEA_URL = "https://data.gov.ro/dataset/a2e2a809-c896-49ca-b7b2-f559627a3516/resource/0a260b52-8b28-48dc-b665-cf25836888c1/download/reteascolara2016-2017.csv"
COORDS_URL = "https://data.gov.ro/dataset/a37f4344-d4fe-40e1-bba7-125e1fea8137/resource/cb27e7f7-065a-4a47-a4eb-9715bfe5e0ce/download/20170327-coordonategps-scoli.xlsx"
RETEA_CACHE = RAW_DIR / "siiir_retea_2016_2017.csv"
COORDS_CACHE = RAW_DIR / "siiir_coords_2017.xlsx"

def _fetch(url: str, dest):
    if dest.exists():
        return
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    dest.write_bytes(r.content)

def main():
    _fetch(RETEA_URL, RETEA_CACHE)
    _fetch(COORDS_URL, COORDS_CACHE)
    retea = pd.read_csv(RETEA_CACHE, dtype=str, sep="\t", encoding="utf-16le")
    coords = pd.read_excel(COORDS_CACHE, dtype=str)
    # Filter to Timiș teaching units only (exclude ISJ/CCD/CJRAE admin entities).
    tm = retea[(retea["Judet"] == "TM") & (retea["Tip unitate"] == "Unitate de învăţământ")].copy()
    # Drop closed units (Data închiderii populated).
    tm = tm[tm["Data închiderii"].isna()].copy()
    merged = tm.merge(coords, left_on="Cod SIIIR", right_on="Cod_SIIIR", how="left")
    merged = merged.rename(columns={
        "Cod SIIIR": "cod_siiir",
        "Denumire": "name",
        "Localitate": "localitate",
        "Localitate superioară": "uat_name",
        "Tip unitate": "tip",
        "Statut": "statut",
        "LAT": "lat",
        "LONG": "lng",
    })
    keep = ["cod_siiir", "name", "localitate", "uat_name", "tip", "statut", "lat", "lng"]
    out_df = merged[keep].copy()
    out_df["data_year"] = "2016-2017"
    if not 500 <= len(out_df) <= 700:
        raise RuntimeError(f"Expected ~600 Timiș schools, got {len(out_df)}")
    with_coords = out_df["lat"].notna().sum()
    if with_coords / len(out_df) < 0.95:
        raise RuntimeError(f"Coord match rate dropped to {with_coords/len(out_df):.0%}, expected >=95%")
    out = INTERMEDIATE_DIR / "schools.csv"
    out_df.to_csv(out, index=False)
    print(f"Wrote {len(out_df)} Timiș schools to {out} ({with_coords} with coords)")

if __name__ == "__main__":
    main()
