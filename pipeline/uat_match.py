"""Map OSM UAT names to SIRUTA codes via normalised name lookup.

OSM names include diacritics + mixed case (e.g. "Timișoara", "Dumbrăvița").
SIRUTA register uses ASCII upper (e.g. "TIMISOARA", "DUMBRAVITA"). The
register also strips the "MUNICIPIUL/ORAȘ/COMUNA" administrative prefix.
"""
import unicodedata
import pandas as pd
from pipeline.config import MANUAL_DIR

PREFIXES = ("MUNICIPIUL ", "ORASUL ", "ORAȘUL ", "COMUNA ", "SECTORUL ")

# OSM uses modern Romanian orthography (post-1993, â mid-word) and full names.
# SIRUTA register preserves pre-1993 spellings (î→I) and quirky abbreviations.
# Map normalised OSM name → normalised register name when they diverge irreparably.
OSM_TO_REGISTER_ALIASES = {
    "SANNICOLAU MARE": "SANICOLAU MARE",
    "SANPETRU MARE": "SINPETRU MARE",
    "FOENI": "FOIENI",
    "BECICHERECU MIC": "BECICHERECUL MIC",
    "BARNA": "BIRNA",
    "VICTOR VLAD DELAMARINA": "V.V.DELAMARINA",
    "MANASTIUR": "MANASTUR",
}

def normalize_name(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper().strip()
    s = s.replace("Ţ", "T").replace("Ș", "S").replace("Ş", "S")
    s = s.replace("Ã", "A").replace("Î", "I").replace("Ă", "A").replace("Â", "A")
    for p in PREFIXES:
        if s.startswith(p):
            s = s[len(p):]
            break
    s = " ".join(s.split())
    return s

def build_timis_name_to_siruta() -> dict[str, str]:
    df = pd.read_csv(MANUAL_DIR / "siruta_register.csv", dtype=str)
    timis = df[df["judet"] == "TIMIS"].copy()
    # Keep only UAT rows (tip_cod in 11=CJ, 12=M, 13=O, 14=C). Drop CJ (county council).
    timis = timis[timis["tip_cod"].isin(["12", "13", "14"])].copy()
    timis["norm"] = timis["denumire"].apply(normalize_name)
    return dict(zip(timis["norm"], timis["siruta"]))

def lookup_siruta(name: str, table: dict[str, str]) -> str | None:
    key = normalize_name(name)
    key = OSM_TO_REGISTER_ALIASES.get(key, key)
    return table.get(key)
