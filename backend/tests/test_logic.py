import math

from logic import (
    calculate_monthly_repayment,
    get_mortgage_breakdown,
    check_property_fit,
    calculate_annual_yield,
)


def test_calculate_monthly_repayment_basic():
    """Loan with zero equity should have positive monthly repayment."""
    price = 1_000_000
    equity = 0
    m = calculate_monthly_repayment(price, equity)
    assert m > 0


def test_get_mortgage_breakdown_respects_first_home_law():
    """Breakdown should reflect 25% equity requirement and correct ratios."""
    price = 1_000_000
    equity = 300_000  # 30% equity
    breakdown = get_mortgage_breakdown(price, equity)
    assert math.isclose(breakdown["required_equity_by_law"], 250_000.0, rel_tol=1e-6)
    assert breakdown["loan_amount"] == 700_000
    assert 0.29 < breakdown["equity_ratio"] < 0.31
    assert breakdown["monthly_repayment"] > 0


def test_check_property_fit_rent_uses_only_max_rent():
    """For rent deals only max_rent is enforced, not equity/max_price."""
    prop = {
        "deal_type": "rent",
        "city": "תל אביב - יפו",
        "rooms": 3,
        "price": 5_000,
    }
    user = {
        "search_type": "rent",
        "target_cities": ["תל אביב - יפו"],
        "rent_room_range_min": 2,
        "rent_room_range_max": 4,
        "max_rent": 6_000,
        "equity": 0,
        "max_price": 1,
    }
    ok, reason = check_property_fit(prop, user)
    assert ok is True
    assert reason == 0


def test_check_property_fit_rent_rejects_above_max_rent():
    prop = {
        "deal_type": "rent",
        "city": "תל אביב - יפו",
        "rooms": 3,
        "price": 7_000,
    }
    user = {
        "search_type": "rent",
        "target_cities": ["תל אביב - יפו"],
        "rent_room_range_min": 2,
        "rent_room_range_max": 4,
        "max_rent": 5_000,
    }
    ok, reason = check_property_fit(prop, user)
    assert ok is False
    assert "מעל התקציב" in str(reason)


def test_check_property_fit_sale_enforces_first_home_equity_and_ratio():
    """Sale deals must honor 25% equity and repayment ratio to income."""
    prop = {
        "deal_type": "sale",
        "city": "פתח תקווה",
        "rooms": 4,
        "price": 1_000_000,
    }
    user = {
        "search_type": "buy",
        "target_cities": ["פתח תקווה"],
        "room_range_min": 3,
        "room_range_max": 5,
        "equity": 200_000,  # פחות מ־25%
        "monthly_income": 20_000,
        "max_repayment_ratio": 0.3,
        "max_price": 1_200_000,
    }
    ok, reason = check_property_fit(prop, user)
    assert ok is False
    assert "25% הון עצמי" in str(reason)

    # הגדלת הון עצמי ל־25% וודא שעוברים את בדיקת החוק (ייתכן שייפלו על יחס החזר)
    user["equity"] = 250_000
    ok2, reason2 = check_property_fit(prop, user)
    # או True עם החזר תקין, או False בגלל יחס החזר — בשני המקרים אין אזכור לחוסר הון עצמי
    assert "25% הון עצמי" not in str(reason2)


def test_calculate_annual_yield_basic():
    y = calculate_annual_yield(price=1_000_000, monthly_rent=4_000)
    assert y == round((12 * 4_000) / 1_000_000 * 100, 2)

