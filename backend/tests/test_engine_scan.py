"""Integration tests for ScanEngine.run_scan_for_user using lightweight mocks."""
import pytest
from engine import ScanEngine


# ─── Mocks ────────────────────────────────────────────────────────────────────

class DummyDB:
    def __init__(self):
        self.logged = []
        self._properties: dict = {}

    def get_avg_price_per_room_by_city(self, user_email):
        return {}

    def add_property(self, prop):
        self.logged.append(("add_property", prop))
        return prop

    def log_search(self, user_email, search_params, results_count, matches_count):
        self.logged.append(("log_search", user_email, search_params, results_count, matches_count))

    def get_active_users(self):
        return []

    def property_exists(self, source, source_id):
        return False

    def get_property_by_source_id(self, source, source_id):
        return None

    def update_property_on_price_drop(self, *args, **kwargs):
        return None


class DummyAI:
    client = None
    model_name = "gemini-2.0-flash"

    def analyze_property(self, prop, user_prefs):
        return {"score": 85, "summary": "נראה טוב", "monthly_repayment_estimate": None}

    def get_neighborhood_insights(self, city, address):
        return {"summary": "שכונה שקטה"}

    def generate_weekly_summary(self, props, user_name):
        return ""


class DummyAILowScore:
    """Returns score below MIN_AI_SCORE_FOR_ALERT so no alert is sent."""
    client = None
    model_name = "gemini-2.0-flash"

    def analyze_property(self, prop, user_prefs):
        return {"score": 10, "summary": "לא מתאים", "monthly_repayment_estimate": None}

    def get_neighborhood_insights(self, city, address):
        return {"summary": ""}

    def generate_weekly_summary(self, props, user_name):
        return ""


class DummyEmail:
    def __init__(self):
        self.alerts_sent = []

    def send_property_alert(self, user_email, properties):
        self.alerts_sent.append((user_email, properties))


def _make_engine(scrapers_output=None, ai=None):
    """Build a ScanEngine with mocked scrapers and DB."""
    db = DummyDB()
    email = DummyEmail()
    ai = ai or DummyAI()
    engine = ScanEngine(db=db, ai=ai, email=email)
    engine._db = db
    engine._email = email
    return engine, db, email


def _patch_scrapers(monkeypatch, properties):
    """Replace _build_scrapers so every deal_type returns a single mock scraper."""
    class MockScraper:
        SOURCE_NAME = "mock"

        def __init__(self, props):
            self._props = props

        def search_all_cities(self, **kwargs):
            return list(self._props)

    monkeypatch.setattr("engine._build_scrapers", lambda deal_type: [MockScraper(properties)])


# ─── Basic scan returns ────────────────────────────────────────────────────────

def test_no_properties_returns_zero_counts(monkeypatch):
    monkeypatch.setattr("engine._build_scrapers", lambda dt: [])
    engine, db, _ = _make_engine()
    user = {
        "email": "u@test.com", "name": "Test",
        "search_type": "buy", "target_cities": ["תל אביב - יפו"],
        "equity": 300_000, "monthly_income": 20_000,
        "room_range_min": 3, "room_range_max": 5,
        "max_price": 1_500_000, "max_repayment_ratio": 0.4,
        "home_index": 1, "loan_term_years": 30,
        "rent_room_range_min": 2, "rent_room_range_max": 5, "max_rent": None,
        "extra_preferences": None,
    }
    result = engine.run_scan_for_user(user)
    assert result["raw_count"] == 0
    assert result["matches_count"] == 0


def test_log_search_always_called(monkeypatch):
    monkeypatch.setattr("engine._build_scrapers", lambda dt: [])
    engine, db, _ = _make_engine()
    user = {
        "email": "u@test.com", "name": "Test",
        "search_type": "buy", "target_cities": [],
        "equity": 300_000, "monthly_income": 20_000,
        "room_range_min": 3, "room_range_max": 5,
        "max_price": 1_500_000, "max_repayment_ratio": 0.4,
        "home_index": 1, "loan_term_years": 30,
        "rent_room_range_min": 2, "rent_room_range_max": 5, "max_rent": None,
        "extra_preferences": None,
    }
    engine.run_scan_for_user(user)
    log_calls = [e for e in db.logged if e[0] == "log_search"]
    assert len(log_calls) == 1


# ─── Sale filtering ────────────────────────────────────────────────────────────

def test_sale_property_passes_fit_and_is_saved(monkeypatch):
    props = [{
        "source": "mock", "source_id": "s1",
        "deal_type": "sale", "city": "פתח תקווה",
        "rooms": 4, "price": 900_000,
    }]
    _patch_scrapers(monkeypatch, props)
    engine, db, email = _make_engine()
    user = {
        "email": "u@test.com", "name": "Test",
        "search_type": "buy", "target_cities": ["פתח תקווה"],
        "equity": 300_000, "monthly_income": 30_000,
        "room_range_min": 3, "room_range_max": 5,
        "max_price": 1_200_000, "max_repayment_ratio": 0.4,
        "home_index": 1, "loan_term_years": 30,
        "rent_room_range_min": 2, "rent_room_range_max": 5, "max_rent": None,
        "extra_preferences": None,
    }
    result = engine.run_scan_for_user(user)
    assert result["raw_count"] == 1
    added = [e for e in db.logged if e[0] == "add_property"]
    assert len(added) == 1


def test_sale_property_filtered_by_price_above_max(monkeypatch):
    props = [{
        "source": "mock", "source_id": "s2",
        "deal_type": "sale", "city": "פתח תקווה",
        "rooms": 4, "price": 2_000_000,
    }]
    _patch_scrapers(monkeypatch, props)
    engine, db, _ = _make_engine()
    user = {
        "email": "u@test.com", "name": "Test",
        "search_type": "buy", "target_cities": ["פתח תקווה"],
        "equity": 300_000, "monthly_income": 20_000,
        "room_range_min": 3, "room_range_max": 5,
        "max_price": 1_500_000, "max_repayment_ratio": 0.4,
        "home_index": 1, "loan_term_years": 30,
        "rent_room_range_min": 2, "rent_room_range_max": 5, "max_rent": None,
        "extra_preferences": None,
    }
    result = engine.run_scan_for_user(user)
    added = [e for e in db.logged if e[0] == "add_property"]
    assert len(added) == 0


def test_buy_search_does_not_scan_rent(monkeypatch):
    """buy search_type should only scan 'sale' deal_type."""
    scanned_types = []

    def fake_build_scrapers(deal_type):
        scanned_types.append(deal_type)
        return []

    monkeypatch.setattr("engine._build_scrapers", fake_build_scrapers)
    engine, db, _ = _make_engine()
    user = {
        "email": "u@test.com", "name": "Test",
        "search_type": "buy", "target_cities": [],
        "equity": 300_000, "monthly_income": 20_000,
        "room_range_min": 3, "room_range_max": 5,
        "max_price": 1_500_000, "max_repayment_ratio": 0.4,
        "home_index": 1, "loan_term_years": 30,
        "rent_room_range_min": 2, "rent_room_range_max": 5, "max_rent": None,
        "extra_preferences": None,
    }
    engine.run_scan_for_user(user)
    assert scanned_types == ["sale"]


def test_rent_search_does_not_scan_sale(monkeypatch):
    scanned_types = []

    def fake_build_scrapers(deal_type):
        scanned_types.append(deal_type)
        return []

    monkeypatch.setattr("engine._build_scrapers", fake_build_scrapers)
    engine, db, _ = _make_engine()
    user = {
        "email": "u@test.com", "name": "Test",
        "search_type": "rent", "target_cities": [],
        "equity": 0, "monthly_income": 0,
        "room_range_min": 2, "room_range_max": 4,
        "max_price": None, "max_repayment_ratio": 0.4,
        "home_index": 1, "loan_term_years": 30,
        "rent_room_range_min": 2, "rent_room_range_max": 4, "max_rent": 6_000,
        "extra_preferences": None,
    }
    engine.run_scan_for_user(user)
    assert scanned_types == ["rent"]


def test_both_search_scans_sale_and_rent(monkeypatch):
    scanned_types = []

    def fake_build_scrapers(deal_type):
        scanned_types.append(deal_type)
        return []

    monkeypatch.setattr("engine._build_scrapers", fake_build_scrapers)
    engine, db, _ = _make_engine()
    user = {
        "email": "u@test.com", "name": "Test",
        "search_type": "both", "target_cities": [],
        "equity": 300_000, "monthly_income": 20_000,
        "room_range_min": 3, "room_range_max": 5,
        "max_price": 1_500_000, "max_repayment_ratio": 0.4,
        "home_index": 1, "loan_term_years": 30,
        "rent_room_range_min": 2, "rent_room_range_max": 4, "max_rent": 6_000,
        "extra_preferences": None,
    }
    engine.run_scan_for_user(user)
    assert set(scanned_types) == {"sale", "rent"}


# ─── Rent filtering ────────────────────────────────────────────────────────────

def test_rent_property_accepted_within_budget(monkeypatch):
    props = [{
        "source": "mock", "source_id": "r1",
        "deal_type": "rent", "city": "תל אביב - יפו",
        "rooms": 3, "price": 5_000,
    }]
    _patch_scrapers(monkeypatch, props)
    engine, db, _ = _make_engine()
    user = {
        "email": "u@test.com", "name": "Test",
        "search_type": "rent", "target_cities": ["תל אביב - יפו"],
        "equity": 0, "monthly_income": 0,
        "room_range_min": 2, "room_range_max": 4,
        "max_price": None, "max_repayment_ratio": 0.4,
        "home_index": 1, "loan_term_years": 30,
        "rent_room_range_min": 2, "rent_room_range_max": 4, "max_rent": 6_000,
        "extra_preferences": None,
    }
    result = engine.run_scan_for_user(user)
    assert result["raw_count"] == 1
    added = [e for e in db.logged if e[0] == "add_property"]
    assert len(added) == 1


def test_rent_property_rejected_above_budget(monkeypatch):
    props = [{
        "source": "mock", "source_id": "r2",
        "deal_type": "rent", "city": "תל אביב - יפו",
        "rooms": 3, "price": 8_000,
    }]
    _patch_scrapers(monkeypatch, props)
    engine, db, _ = _make_engine()
    user = {
        "email": "u@test.com", "name": "Test",
        "search_type": "rent", "target_cities": ["תל אביב - יפו"],
        "equity": 0, "monthly_income": 0,
        "room_range_min": 2, "room_range_max": 4,
        "max_price": None, "max_repayment_ratio": 0.4,
        "home_index": 1, "loan_term_years": 30,
        "rent_room_range_min": 2, "rent_room_range_max": 4, "max_rent": 6_000,
        "extra_preferences": None,
    }
    result = engine.run_scan_for_user(user)
    added = [e for e in db.logged if e[0] == "add_property"]
    assert len(added) == 0


# ─── profile_type and home_index ──────────────────────────────────────────────

def test_second_home_requires_50_pct_equity(monkeypatch):
    props = [{
        "source": "mock", "source_id": "h2",
        "deal_type": "sale", "city": "חיפה",
        "rooms": 4, "price": 1_000_000,
    }]
    _patch_scrapers(monkeypatch, props)
    engine, db, _ = _make_engine()
    user = {
        "email": "u@test.com", "name": "Test",
        "search_type": "buy", "target_cities": ["חיפה"],
        "equity": 400_000,        # 40% — ok for first home but not second
        "monthly_income": 30_000,
        "room_range_min": 3, "room_range_max": 5,
        "max_price": 1_500_000, "max_repayment_ratio": 0.4,
        "home_index": 2, "loan_term_years": 30,  # second home → needs 50%
        "rent_room_range_min": 2, "rent_room_range_max": 4, "max_rent": None,
        "extra_preferences": None,
    }
    result = engine.run_scan_for_user(user)
    added = [e for e in db.logged if e[0] == "add_property"]
    assert len(added) == 0  # rejected due to insufficient equity


def test_profile_type_stored_in_user_prefs(monkeypatch):
    """Engine should pass profile_type through user_prefs without error."""
    monkeypatch.setattr("engine._build_scrapers", lambda dt: [])
    engine, db, _ = _make_engine()
    for profile in ("HOME_BUYER", "INVESTOR", "CASH_FLOW_MAXIMIZER"):
        user = {
            "email": "u@test.com", "name": "Test",
            "search_type": "buy", "target_cities": [],
            "equity": 300_000, "monthly_income": 20_000,
            "room_range_min": 3, "room_range_max": 5,
            "max_price": 1_500_000, "max_repayment_ratio": 0.4,
            "home_index": 1, "loan_term_years": 30,
            "profile_type": profile,
            "rent_room_range_min": 2, "rent_room_range_max": 4, "max_rent": None,
            "extra_preferences": None,
        }
        result = engine.run_scan_for_user(user)
        assert result["raw_count"] == 0  # no crash

