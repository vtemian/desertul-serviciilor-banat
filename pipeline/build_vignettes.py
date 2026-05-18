"""Generate 5 worst-served vignette drafts. Vlad humanizes before launch."""
import json
import pandas as pd
from pipeline.config import INTERMEDIATE_DIR, WEB_DATA_DIR
from pipeline.uat_match import build_timis_name_to_siruta, lookup_siruta


def render(row, name_to_siruta, pop_by_siruta) -> dict:
    name = row["name"]
    siruta = lookup_siruta(name, name_to_siruta) or ""
    pop = int(pop_by_siruta.get(siruta, 0))
    d_school_km = (row["nearest_school_m"] or 0) / 1000
    gp_cnt = row.get("gp_count")
    gp_known = isinstance(gp_cnt, (int, float)) and str(gp_cnt) not in ("", "nan")
    gp_cnt_int = int(gp_cnt) if gp_known else None
    pop_ro = f"{pop:,}".replace(",", ".")  # Romanian thousands separator
    pop_en = f"{pop:,}"
    return {
        "siruta": siruta,
        "name": name,
        "composite_score": round(float(row["composite_score"]), 1),
        "population": pop,
        "headline": {
            "ro": (f"În {name}, cei aproximativ {pop_ro} locuitori au în medie "
                   f"{d_school_km:.1f} km până la cea mai apropiată școală"
                   + (f" și {gp_cnt_int} medic{'i' if gp_cnt_int != 1 else ''} de familie pe întreaga comună." if gp_known
                      else ". (Numărul medicilor de familie va fi adăugat în v0.1.)")
                  ),
            "en": (f"In {name}, roughly {pop_en} residents live an average of "
                   f"{d_school_km:.1f} km from the nearest school"
                   + (f", with {gp_cnt_int} family doctor{'s' if gp_cnt_int != 1 else ''} serving the entire commune." if gp_known
                      else ". (Family-doctor counts will be added in v0.1.)")
                  ),
        },
        "draft_only": True,
    }


def main():
    df = pd.read_csv(INTERMEDIATE_DIR / "uat_scores.csv")
    df = df.dropna(subset=["composite_score"]).sort_values("composite_score").head(5)
    name_to_siruta = build_timis_name_to_siruta()
    pop_df = pd.read_csv(INTERMEDIATE_DIR / "population.csv", dtype={"siruta": str})
    pop_by_siruta = dict(zip(pop_df["siruta"], pop_df["pop_total"]))
    rows = [render(r, name_to_siruta, pop_by_siruta) for _, r in df.iterrows()]
    out = WEB_DATA_DIR / "vignettes.json"
    out.write_text(json.dumps({"vignettes": rows}, ensure_ascii=False, indent=2))
    print(f"Wrote {len(rows)} vignettes to {out}. Vlad: humanize before launch.")


if __name__ == "__main__":
    main()
