from pipeline.compute_scores import school_score, gp_score, hospital_score, composite


def test_school_score_close():
    assert school_score(800) > 90


def test_school_score_far():
    assert school_score(8000) == 0
    assert school_score(15000) == 0


def test_gp_score_well_supplied():
    assert gp_score(pop_total=1500, gp_count=1) >= 95


def test_gp_score_underserved():
    assert gp_score(pop_total=5000, gp_count=1) == 0


def test_gp_score_data_missing():
    import math
    assert math.isnan(gp_score(pop_total=2000, gp_count=None))


def test_hospital_score_close():
    assert hospital_score(8000) > 90


def test_composite_renormalizes_on_nan():
    # 0.4*80 + 0.4*60 = 56; remaining weight 0.8 -> 70
    assert abs(composite(school=80, gp=60, hospital=float("nan")) - 70) < 1e-6
