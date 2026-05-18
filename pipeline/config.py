from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERMEDIATE_DIR = DATA_DIR / "intermediate"
MANUAL_DIR = DATA_DIR / "manual"
WEB_DATA_DIR = REPO_ROOT / "web" / "data"

for d in (RAW_DIR, INTERMEDIATE_DIR, MANUAL_DIR, WEB_DATA_DIR):
    d.mkdir(parents=True, exist_ok=True)

TIMIS_JUDET_CODES = {"TIMIS", "TIMIȘ", "TM"}
ROMANIA_STEREO_70 = "EPSG:3844"
WGS84 = "EPSG:4326"

SCORE_WEIGHTS = {"school": 0.4, "gp": 0.4, "hospital": 0.2}

ER_HOSPITALS = [
    {"name": "Spitalul Clinic Județean de Urgență Timișoara", "lat": 45.7460, "lng": 21.2310, "uat_name": "Timișoara"},
    {"name": "Spitalul Clinic Municipal de Urgență Timișoara", "lat": 45.7530, "lng": 21.2240, "uat_name": "Timișoara"},
    {"name": "Spitalul Municipal Lugoj",                       "lat": 45.6890, "lng": 21.9030, "uat_name": "Lugoj"},
    {"name": "Spitalul Orășenesc Făget",                       "lat": 45.8530, "lng": 22.1780, "uat_name": "Făget"},
]
