import math
import pytest

from logic import (
    calculate_monthly_repayment,
    get_mortgage_breakdown,
    check_property_fit,
    calculate_annual_yield,
    estimate_monthly_rent,
    get_market_value_label,
)


# ─── calculate_monthly_repayment ───────────────────────────────────────────────

class TestCalculateMonthlyRepayment:
    def test_basic_positive_repayment(self):
        assert calculate_monthly_repayment(1_000_000, 0) > 0

    def test_no_loan_when_equity_covers_price(self):
        assert calculate_monthly_repayment(1_000_000, 1_000_000) == 0

    def test_longer_term_means_lower_repayment(self):
        short = calculate_monthly_repayment(1_000_000, 250_000, years=15)
        long = calculate_monthly_repayment(1_000_000, 250_000, years=30)
        assert short > long

    def test_higher_interest_means_higher_repayment(self):
        low = calculate_monthly_repayment(1_000_000, 250_000, interest=0.03)
        high = calculate_monthly_repayment(1_000_000, 250_000, interest=0.07)
        assert high > low

    def test_custom_loan_term_20_years(self):
        r20 = calculate_monthly_repayment(1_000_000, 250_000, years=20)
        r30 = calculate_monthly_repayment(1_000_000, 250_000, years=30)
        assert r20 > r30

    def test_repayment_formula_accuracy(self):
        price, equity, interest, years = 800_000, 200_000, 0.045, 30
        loan = price - equity
        r = interest / 12
        n = years * 12
        expected = loan * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
        result = calculate_monthly_repayment(price, equity, interest=interest, years=years)
        assert math.isclose(result, expected, rel_tol=1e-6)


# ─── get_mortgage_breakdown ────────────────────────────────────────────────────

class TestGetMortgageBreakdown:
    def test_first_home_equity_requirement(self):
        bd = get_mortgage_breakdown(1_000_000, 300_000)
        assert math.isclose(bd["required_equity_by_law"], 250_000, rel_tol=1e-6)

    def test_loan_amount_equals_price_minus_equity(self):
        bd = get_mortgage_breakdown(1_200_000, 400_000)
        assert bd["loan_amount"] == 800_000

    def test_equity_ratio(self):
        bd = get_mortgage_breakdown(1_000_000, 300_000)
        assert math.isclose(bd["equity_ratio"], 0.3, rel_tol=1e-6)

    def test_monthly_repayment_positive(self):
        bd = get_mortgage_breakdown(1_000_000, 250_000)
        assert bd["monthly_repayment"] > 0

    def test_custom_years_affects_repayment(self):
        bd15 = get_mortgage_breakdown(1_000_000, 250_000, years=15)
        bd30 = get_mortgage_breakdown(1_000_000, 250_000, years=30)
        assert bd15["monthly_repayment"] > bd30["monthly_repayment"]


# ─── check_property_fit ────────────────────────────────────────────────────────

class TestCheckPropertyFitSale:
    BASE_PROP = {
        "deal_type": "sale",
        "city": "פתח תקווה",
        "rooms": 4,
        "price": 1_000_000,
    }
    BASE_USER = {
        "search_type": "buy",
        "target_cities": ["פתח תקווה"],
        "room_range_min": 3,
        "room_range_max": 5,
        "equity": 300_000,
        "monthly_income": 20_000,
        "max_repayment_ratio": 0.4,
        "max_price": 1_500_000,
        "home_index": 1,
    }

    def test_valid_sale_passes(self):
        ok, _ = check_property_fit(self.BASE_PROP, self.BASE_USER)
        assert ok is True

    def test_sale_rejected_when_price_above_max(self):
        prop = {**self.BASE_PROP, "price": 2_000_000}
        ok, reason = check_property_fit(prop, self.BASE_USER)
        assert ok is False
        assert "מחיר" in str(reason) or "תקציב" in str(reason)

    def test_sale_rejected_for_insufficient_equity_first_home(self):
        user = {**self.BASE_USER, "equity": 200_000}  # 20% < 25%
        ok, reason = check_property_fit(self.BASE_PROP, user)
        assert ok is False
        assert "25%" in str(reason)

    def test_sale_rejected_for_insufficient_equity_second_home(self):
        user = {**self.BASE_USER, "equity": 400_000, "home_index": 2}  # 40% < 50%
        ok, reason = check_property_fit(self.BASE_PROP, user)
        assert ok is False
        assert "50%" in str(reason)

    def test_second_home_passes_with_50_pct_equity(self):
        user = {**self.BASE_USER, "equity": 500_001, "home_index": 2}
        ok, _ = check_property_fit(self.BASE_PROP, user)
        assert ok is True

    def test_sale_rejected_when_repayment_exceeds_ratio(self):
        # Very low income → repayment > 40%
        user = {**self.BASE_USER, "monthly_income": 3_000}
        ok, reason = check_property_fit(self.BASE_PROP, user)
        assert ok is False
        assert "בנקים" in str(reason) or "החזר" in str(reason)

    def test_sale_rejected_when_rooms_outside_range(self):
        prop = {**self.BASE_PROP, "rooms": 7}
        ok, reason = check_property_fit(prop, self.BASE_USER)
        assert ok is False
        assert "חדרים" in str(reason)

    def test_sale_rejected_when_city_not_in_list(self):
        prop = {**self.BASE_PROP, "city": "אילת"}
        ok, reason = check_property_fit(prop, self.BASE_USER)
        assert ok is False
        assert "אזור" in str(reason)

    def test_buy_search_rejects_rent_property(self):
        prop = {**self.BASE_PROP, "deal_type": "rent"}
        ok, reason = check_property_fit(prop, self.BASE_USER)
        assert ok is False
        assert "מכירה" in str(reason)

    def test_sale_rejected_when_no_income(self):
        user = {**self.BASE_USER, "monthly_income": 0}
        ok, reason = check_property_fit(self.BASE_PROP, user)
        assert ok is False
        assert "הכנסה" in str(reason)

    def test_loan_term_affects_fit(self):
        """Short loan term increases repayment and can flip affordability."""
        user_short = {**self.BASE_USER, "monthly_income": 8_000, "loan_term_years": 10}
        user_long = {**self.BASE_USER, "monthly_income": 8_000, "loan_term_years": 30}
        ok_short, _ = check_property_fit(self.BASE_PROP, user_short)
        ok_long, _ = check_property_fit(self.BASE_PROP, user_long)
        # long term should be more affordable
        assert (not ok_short) or ok_long


class TestCheckPropertyFitRent:
    BASE_PROP = {
        "deal_type": "rent",
        "city": "תל אביב - יפו",
        "rooms": 3,
        "price": 5_000,
    }
    BASE_USER = {
        "search_type": "rent",
        "target_cities": ["תל אביב - יפו"],
        "rent_room_range_min": 2,
        "rent_room_range_max": 4,
        "max_rent": 6_000,
        "equity": 0,
        "max_price": 1,
    }

    def test_valid_rent_passes(self):
        ok, reason = check_property_fit(self.BASE_PROP, self.BASE_USER)
        assert ok is True
        assert reason == 0

    def test_rent_rejected_above_max_rent(self):
        prop = {**self.BASE_PROP, "price": 8_000}
        ok, reason = check_property_fit(prop, self.BASE_USER)
        assert ok is False
        assert "מעל התקציב" in str(reason)

    def test_rent_search_rejects_sale_property(self):
        prop = {**self.BASE_PROP, "deal_type": "sale"}
        ok, reason = check_property_fit(prop, self.BASE_USER)
        assert ok is False
        assert "השכרה" in str(reason)

    def test_rent_ignores_equity(self):
        user = {**self.BASE_USER, "equity": 0, "max_price": 1}
        ok, _ = check_property_fit(self.BASE_PROP, user)
        assert ok is True

    def test_rent_rejected_wrong_room_count(self):
        prop = {**self.BASE_PROP, "rooms": 6}
        ok, reason = check_property_fit(prop, self.BASE_USER)
        assert ok is False
        assert "חדרים" in str(reason)


# ─── calculate_annual_yield ────────────────────────────────────────────────────

class TestCalculateAnnualYield:
    def test_basic_yield(self):
        y = calculate_annual_yield(1_000_000, 4_000)
        assert y == round(12 * 4_000 / 1_000_000 * 100, 2)

    def test_zero_price_returns_zero(self):
        assert calculate_annual_yield(0, 4_000) == 0.0

    def test_zero_rent_returns_zero(self):
        assert calculate_annual_yield(1_000_000, 0) == 0.0

    def test_high_yield_property(self):
        y = calculate_annual_yield(500_000, 6_000)
        assert y > 10


# ─── estimate_monthly_rent ─────────────────────────────────────────────────────

class TestEstimateMonthlyRent:
    def test_returns_positive_for_known_city_with_sqm(self):
        prop = {"city": "תל אביב - יפו", "size_sqm": 80}
        rent = estimate_monthly_rent(prop)
        assert rent is not None and rent > 0

    def test_falls_back_to_rooms_when_no_sqm(self):
        prop = {"city": "חיפה", "rooms": 3}
        rent = estimate_monthly_rent(prop)
        assert rent is not None and rent > 0

    def test_unknown_city_still_returns_value(self):
        prop = {"city": "עיר_לא_קיימת", "rooms": 3}
        rent = estimate_monthly_rent(prop)
        assert rent is not None and rent > 0

    def test_tel_aviv_higher_than_beer_sheva(self):
        ta = estimate_monthly_rent({"city": "תל אביב - יפו", "size_sqm": 70})
        bs = estimate_monthly_rent({"city": "באר שבע", "size_sqm": 70})
        assert ta > bs


# ─── get_market_value_label ────────────────────────────────────────────────────

class TestGetMarketValueLabel:
    def test_below_market(self):
        label = get_market_value_label(800_000, 4, 250_000)
        assert label == "Below Market Value"

    def test_overpriced(self):
        label = get_market_value_label(1_200_000, 4, 250_000)
        assert label == "Overpriced"

    def test_fair_price(self):
        label = get_market_value_label(1_000_000, 4, 250_000)
        assert label == "Fair Price"

    def test_missing_avg_returns_fair(self):
        assert get_market_value_label(1_000_000, 4, None) == "Fair Price"

    def test_zero_rooms_returns_fair(self):
        assert get_market_value_label(1_000_000, 0, 250_000) == "Fair Price"
