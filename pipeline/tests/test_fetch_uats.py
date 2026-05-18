from pipeline.fetch_uats import normalize_features


def test_normalize_features_preserves_name_and_sets_judet():
    raw = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": None, "properties": {
            "id": "relation/123", "tags": {"name": "Timișoara", "admin_level": "8", "wikidata": "Q83022"}}}
    ]}
    out = normalize_features(raw)
    assert len(out["features"]) == 1
    p = out["features"][0]["properties"]
    assert p["name"] == "Timișoara"
    assert p["judet"] == "TIMIȘ"
    assert p["admin_level"] == "8"
    assert p["wikidata"] == "Q83022"
