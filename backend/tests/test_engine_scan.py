from engine import ScanEngine


class DummyDB:
    def __init__(self) -> None:
        self.logged = []

    def get_avg_price_per_room_by_city(self, user_email: str):
        return {}

    def add_property(self, prop: dict):
        # In this basic test we don't expect any properties to be added
        self.logged.append(("add_property", prop))
        return prop

    def log_search(self, user_email: str, search_params: dict, results_count: int, matches_count: int):
        self.logged.append(
            ("log_search", user_email, search_params, results_count, matches_count)
        )

    def get_active_users(self):
        return []


class DummyAI:
    client = None

    def analyze_property(self, prop: dict, user_prefs: dict):
        return {"score": 0, "summary": "", "monthly_repayment_estimate": None}

    def get_neighborhood_insights(self, city: str, address: str | None):
        return {"summary": ""}

    def generate_weekly_summary(self, props: list[dict], user_name: str):
        return ""


class DummyEmail:
    def send_property_alert(self, user_email: str, properties: list[dict]):
        return None


def test_scan_engine_with_no_scrapers_returns_zero_counts(monkeypatch):
    """If scrapers return no properties, engine should still log search and return 0 counts."""

    def fake_build_scrapers(deal_type: str):
        return []  # no external calls in unit test

    monkeypatch.setattr("engine._build_scrapers", fake_build_scrapers)

    db = DummyDB()
    ai = DummyAI()
    email = DummyEmail()
    engine = ScanEngine(db=db, ai=ai, email=email)

    user = {
        "email": "test@example.com",
        "name": "Test User",
        "search_type": "buy",
        "target_cities": ["תל אביב - יפו"],
        "equity": 300_000,
        "monthly_income": 20_000,
        "room_range_min": 3,
        "room_range_max": 4,
        "max_price": 1_500_000,
        "rent_room_range_min": 2,
        "rent_room_range_max": 4,
        "max_rent": 6_000,
        "extra_preferences": None,
    }

    result = engine.run_scan_for_user(user)

    assert isinstance(result, dict)
    assert result["raw_count"] == 0
    assert result["matches_count"] == 0

    # Verify that log_search was called once
    log_calls = [e for e in db.logged if e[0] == "log_search"]
    assert len(log_calls) == 1
    _, email_logged, search_params, results_count, matches_count = log_calls[0]
    assert email_logged == "test@example.com"
    assert results_count == 0
    assert matches_count == 0
    assert search_params["deal_types"] == ["sale"]

