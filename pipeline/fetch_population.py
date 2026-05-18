"""Fetch 2021 census resident population per UAT from recensamantromania.ro."""
import csv
import requests
import pandas as pd
from pipeline.config import RAW_DIR, INTERMEDIATE_DIR

URL = "https://www.recensamantromania.ro/wp-content/uploads/2022/02/Populatia-rezidenta-tinta-estimata-la-1-decembrie-2021_UAT_site-RPL.xlsx"
SRC = RAW_DIR / "rpl2021_pop_uat.xlsx"


def _to_int(x: str) -> int:
    return int(str(x).replace(" ", "").replace(",", "").strip() or 0)


def normalize_row(raw: dict) -> dict | None:
    siruta = (raw.get("siruta") or "").strip()
    if not siruta:  # judet/urban/rural aggregate rows have no SIRUTA
        return None
    return {
        "siruta": siruta,
        "name": (raw.get("denumire_uat") or "").strip(),
        "judet_code": (raw.get("cod_judet") or "").strip(),
        "pop_total": _to_int(raw.get("pop_rezidenta") or "0"),
    }


def fetch():
    if not SRC.exists():
        r = requests.get(URL, timeout=60)
        r.raise_for_status()
        SRC.write_bytes(r.content)


def load_localities() -> list[dict]:
    xl = pd.ExcelFile(SRC)
    # Sheet name has a trailing space upstream; match by stripped form to survive a future fix.
    sheet = next((s for s in xl.sheet_names if s.strip().upper() == "LOCALITATI"), None)
    if sheet is None:
        raise RuntimeError(f"No LOCALITATI sheet in {SRC}; got {xl.sheet_names}")
    df = pd.read_excel(xl, sheet_name=sheet, dtype=str, header=1)
    df.columns = ["cod_judet", "denumire_uat", "siruta", "pop_rezidenta",
                  "_unused", "loc_dispersate", "loc_izolate"][: len(df.columns)]
    df = df.fillna("")  # pd.read_excel leaves empty cells as float NaN despite dtype=str
    rows = (normalize_row(r) for r in df.to_dict(orient="records"))
    return [r for r in rows if r is not None]


def main():
    fetch()
    rows = load_localities()
    timis = [r for r in rows if r["judet_code"] == "37"]
    if not 95 <= len(timis) <= 105:
        raise RuntimeError(f"Expected ~99 Timiș UATs, got {len(timis)}")
    out = INTERMEDIATE_DIR / "population.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["siruta", "name", "judet_code", "pop_total"])
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} UAT rows ({len(timis)} Timiș) to {out}")


if __name__ == "__main__":
    main()
