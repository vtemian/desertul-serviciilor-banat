"""Materialize the 4 ER hospitals in Timiș as a geocoded CSV.

Hand-geocoded constants live in pipeline.config.ER_HOSPITALS (~10m precision,
sufficient for "distance to nearest ER" coarse scoring).
"""
import csv
from pipeline.config import ER_HOSPITALS, INTERMEDIATE_DIR


def main():
    out = INTERMEDIATE_DIR / "hospitals.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["name", "lat", "lng", "uat_name", "has_emergency"])
        w.writeheader()
        for h in ER_HOSPITALS:
            w.writerow({**h, "has_emergency": True})
    print(f"Wrote {len(ER_HOSPITALS)} ER hospitals to {out}")


if __name__ == "__main__":
    main()
