from app.services.narrative import build_variance_narrative


def test_build_variance_narrative_basic():
    variance = {
        "net_income_change": -80.0,
        "explained_pct": 100.0,
        "drivers": {
            "revenue_impact": -60.0,
            "margin_impact": -90.0,
            "opex_impact": 50.0,
            "residual": 0.0,
        },
    }

    text = build_variance_narrative(
        base_upload_id="base1",
        compare_upload_id="comp1",
        variance=variance,
        top_n=3,
    )

    assert "Net income" in text
    assert "Top drivers" in text
    assert "Margin Impact" in text or "Margin impact" in text
