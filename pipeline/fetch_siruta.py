"""Fetch SIRUTA register from data.gov.ro CKAN and convert to CSV."""
import io
import requests
import pandas as pd
from pipeline.config import MANUAL_DIR

PACKAGE_API = "https://data.gov.ro/api/3/action/package_show?id=unitati-administrativ-teritoriale-coduri-siruta"

def main():
    meta = requests.get(PACKAGE_API, timeout=30).json()
    res = next(r for r in meta["result"]["resources"]
               if r["format"].lower() in ("csv", "xlsx", "xls") and "siruta" in r["url"].lower())
    fmt = res["format"].lower()
    r = requests.get(res["url"], timeout=60)
    r.raise_for_status()
    if fmt in ("xls", "xlsx"):
        raw_path = MANUAL_DIR / f"siruta_register_raw.{fmt}"
        raw_path.write_bytes(r.content)
        # Source xls layout: rows 0-2 blank, row 3 main headers, rows 4-5 blank,
        # row 6 sub-headers (Cod/Nume for Tipul UAT), row 7 column-letter labels
        # (a,b,c,...), row 8+ real data. 8 raw columns; col 0 and col 7 are blank.
        df = pd.read_excel(io.BytesIO(r.content), dtype=str, header=None, skiprows=8)
        df.columns = ["_blank0", "cod_judet", "judet", "tip_cod", "tip_nume", "siruta", "denumire", "_blank1"]
        df = df[["cod_judet", "judet", "tip_cod", "tip_nume", "siruta", "denumire"]]
        df = df.dropna(how="all").reset_index(drop=True)
        out = MANUAL_DIR / "siruta_register.csv"
        df.to_csv(out, index=False)
        print(f"Wrote {raw_path} ({raw_path.stat().st_size} bytes) and {out} ({out.stat().st_size} bytes, {len(df)} rows, cols={list(df.columns)})")
    else:
        out = MANUAL_DIR / "siruta_register.csv"
        out.write_bytes(r.content)
        print(f"Wrote {out} ({len(r.content)} bytes)")

if __name__ == "__main__":
    main()
