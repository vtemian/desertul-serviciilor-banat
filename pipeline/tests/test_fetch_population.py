from pipeline.fetch_population import normalize_row


def test_normalize_row_keeps_uat_with_siruta():
    raw = {"cod_judet": "37", "denumire_uat": "MUNICIPIUL TIMISOARA",
           "siruta": "155243", "pop_rezidenta": "300344"}
    assert normalize_row(raw) == {"siruta": "155243", "name": "MUNICIPIUL TIMISOARA",
                                  "judet_code": "37", "pop_total": 300344}


def test_normalize_row_skips_aggregates_without_siruta():
    raw = {"cod_judet": "37", "denumire_uat": "TIMIS", "siruta": "", "pop_rezidenta": "707867"}
    assert normalize_row(raw) is None
