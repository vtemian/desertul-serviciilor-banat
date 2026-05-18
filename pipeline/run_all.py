"""Run the full pipeline end to end.

Steps that depend on the CAS Timiș scraper (fetch_gps, geocode_gps) only run
when their precursor data files exist; until B6/B7 are unblocked they are
silently skipped, which lets the rest of the pipeline regenerate cleanly.
"""
import subprocess
import sys
from pathlib import Path

from pipeline.config import INTERMEDIATE_DIR

# (module, optional, precondition_path_or_None)
STEPS = [
    ("pipeline.fetch_uats",       False, None),
    ("pipeline.fetch_siruta",     False, None),
    ("pipeline.fetch_population", False, None),
    ("pipeline.fetch_schools",    False, None),
    ("pipeline.fetch_hospitals",  False, None),
    # GP scraping + geocoding deferred until CAS Timiș endpoint recon (B6) lands.
    ("pipeline.fetch_gps",        True,  Path("pipeline/fetch_gps.py")),
    ("pipeline.geocode_gps",      True,  INTERMEDIATE_DIR / "gps.csv"),
    ("pipeline.compute_distances", False, None),
    ("pipeline.compute_scores",   False, None),
    ("pipeline.build_geojson",    False, None),
    ("pipeline.build_services",   False, None),
    ("pipeline.build_vignettes",  False, None),
]


def main() -> int:
    for mod, optional, gate in STEPS:
        if gate is not None and not gate.exists():
            label = "SKIP (optional, missing precondition)" if optional else "SKIP (no precondition)"
            print(f"\n=== {mod} === [{label}: {gate}]")
            continue
        print(f"\n=== {mod} ===")
        rc = subprocess.call([sys.executable, "-m", mod])
        if rc != 0:
            print(f"\nStep {mod} failed with exit code {rc}", file=sys.stderr)
            return rc
    print("\nPipeline complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
