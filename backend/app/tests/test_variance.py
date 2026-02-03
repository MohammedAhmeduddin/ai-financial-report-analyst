import pytest

from app.services.variance import compute_variance_drivers


def test_variance_drivers_happy_path():
    base = {
        "revenue": 1000,
        "gross_profit": 600,
        "operating_income": 300,
        "net_income": 200,
    }
    compare = {
        "revenue": 900,
        "gross_profit": 450,
        "operating_income": 200,
        "net_income": 120,
    }

    out = compute_variance_drivers(base, compare)

    assert out["net_income_change"] == pytest.approx(-80.0)

    d = out["drivers"]
    # base GM = 600/1000 = 0.6
    assert d["revenue_impact"] == pytest.approx((900 - 1000) * 0.6)  # -60
    # expected GP = 600 + (-60) = 540, actual 450 => margin impact -90
    assert d["margin_impact"] == pytest.approx(450 - 540)  # -90

    # opex = gp - oi
    # base opex 300, compare opex 250 => delta -50 => opex_impact = +50
    assert d["opex_impact"] == pytest.approx(50)

    # other = change in (NI - OI)
    # base below = -100, compare below = -80 => other +20
    assert d["other"] == pytest.approx(20)

    # residual reconciles to net income change
    explained = d["revenue_impact"] + d["margin_impact"] + d["opex_impact"] + d["other"]
    assert d["residual"] == pytest.approx(out["net_income_change"] - explained)


def test_variance_requires_net_income():
    base = {"revenue": 100}
    compare = {"revenue": 120, "net_income": 10}
    with pytest.raises(ValueError):
        compute_variance_drivers(base, compare)


def test_variance_handles_missing_components_with_residual():
    base = {"net_income": 10}
    compare = {"net_income": 25}

    out = compute_variance_drivers(base, compare)
    assert out["net_income_change"] == 15
    assert out["drivers"]["residual"] == 15
    assert out["drivers"]["revenue_impact"] is None
    assert out["drivers"]["margin_impact"] is None
    assert out["drivers"]["opex_impact"] is None
    assert out["drivers"]["other"] is None
