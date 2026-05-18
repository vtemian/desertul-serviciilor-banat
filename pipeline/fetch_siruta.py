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
        # Probe for the header row by content rather than hardcoding skiprows.
        # Real data sits 2 rows below "Cod judet" (sub-header + column-letter row).
        probe = pd.read_excel(io.BytesIO(r.content), dtype=str, header=None, nrows=20)
        header_row = next(
            (i for i, row in probe.iterrows()
             if row.astype(str).str.contains("Cod judet", case=False, na=False).any()),
            None,
        )
        if header_row is None:
            raise RuntimeError("SIRUTA xls layout changed: no 'Cod judet' header found in first 20 rows")
        df = pd.read_excel(io.BytesIO(r.content), dtype=str, header=None, skiprows=header_row + 5)
        df.columns = ["_blank0", "cod_judet", "judet", "tip_cod", "tip_nume", "siruta", "denumire", "_blank1"]
        df = df[["cod_judet", "judet", "tip_cod", "tip_nume", "siruta", "denumire"]]
        df = df.dropna(how="all").reset_index(drop=True)
        # Fail loud if rows are misaligned (catches a future layout shift before garbage hits git).
        siruta_ok = df["siruta"].fillna("").str.match(r"^\d{1,7}$").mean()
        if siruta_ok < 0.95:
            raise RuntimeError(
                f"SIRUTA column looks misaligned: only {siruta_ok:.0%} of rows match numeric pattern. "
                "Upstream xls layout may have changed.")
        out = MANUAL_DIR / "siruta_register.csv"
        df.to_csv(out, index=False)
        print(f"Wrote {raw_path} ({raw_path.stat().st_size} bytes) and {out} ({out.stat().st_size} bytes, {len(df)} rows, cols={list(df.columns)})")
    else:
        out = MANUAL_DIR / "siruta_register.csv"
        out.write_bytes(r.content)
        print(f"Wrote {out} ({len(r.content)} bytes)")

if __name__ == "__main__":
    main()
