"""Unit tests for properties router logic (view=latest|all, deal_type, city filters)."""
import pytest
from unittest.mock import MagicMock, patch

from api.routers.properties import list_properties


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_prop(city="תל אביב - יפו", deal_type="sale", price=1_000_000):
    return {
        "_id": None,
        "source": "mock",
        "source_id": "x1",
        "deal_type": deal_type,
        "city": city,
        "rooms": 4,
        "price": price,
        "listing_url": "https://example.com",
    }


def _make_db(all_props=None, latest_props=None):
    db = MagicMock()
    db.get_all_properties_for_user.return_value = all_props or []
    db.get_latest_scan_properties.return_value = latest_props or []
    return db


# ─── view=all ─────────────────────────────────────────────────────────────────

def test_view_all_calls_get_all_properties():
    db = _make_db(all_props=[_make_prop()])
    result = list_properties(email="u@test.com", db=db, deal_type=None, city=None, limit=50, view="all")
    db.get_all_properties_for_user.assert_called_once_with("u@test.com", limit=50)
    db.get_latest_scan_properties.assert_not_called()
    assert len(result) == 1


def test_view_latest_calls_get_latest_scan_properties():
    db = _make_db(latest_props=[_make_prop()])
    result = list_properties(email="u@test.com", db=db, deal_type=None, city=None, limit=50, view="latest")
    db.get_latest_scan_properties.assert_called_once_with("u@test.com", limit=50)
    db.get_all_properties_for_user.assert_not_called()
    assert len(result) == 1


def test_default_view_is_all():
    db = _make_db(all_props=[_make_prop()])
    list_properties(email="u@test.com", db=db, deal_type=None, city=None, limit=50, view="all")
    db.get_all_properties_for_user.assert_called_once()


# ─── deal_type filter ─────────────────────────────────────────────────────────

def test_deal_type_sale_filter_excludes_rent():
    props = [
        _make_prop(deal_type="sale"),
        _make_prop(deal_type="rent"),
    ]
    db = _make_db(all_props=props)
    result = list_properties(email="u@test.com", db=db, deal_type="sale", city=None, limit=50, view="all")
    assert all(p["deal_type"] == "sale" for p in result)
    assert len(result) == 1


def test_deal_type_rent_filter_excludes_sale():
    props = [
        _make_prop(deal_type="sale"),
        _make_prop(deal_type="rent"),
    ]
    db = _make_db(all_props=props)
    result = list_properties(email="u@test.com", db=db, deal_type="rent", city=None, limit=50, view="all")
    assert all(p["deal_type"] == "rent" for p in result)
    assert len(result) == 1


def test_no_deal_type_filter_returns_all():
    props = [_make_prop(deal_type="sale"), _make_prop(deal_type="rent")]
    db = _make_db(all_props=props)
    result = list_properties(email="u@test.com", db=db, deal_type=None, city=None, limit=50, view="all")
    assert len(result) == 2


# ─── city filter ──────────────────────────────────────────────────────────────

def test_city_filter_works():
    props = [
        _make_prop(city="תל אביב - יפו"),
        _make_prop(city="חיפה"),
    ]
    db = _make_db(all_props=props)
    result = list_properties(email="u@test.com", db=db, deal_type=None, city="חיפה", limit=50, view="all")
    assert len(result) == 1
    assert result[0]["city"] == "חיפה"


def test_city_and_deal_type_combined_filter():
    props = [
        _make_prop(city="תל אביב - יפו", deal_type="sale"),
        _make_prop(city="תל אביב - יפו", deal_type="rent"),
        _make_prop(city="חיפה", deal_type="sale"),
    ]
    db = _make_db(all_props=props)
    result = list_properties(
        email="u@test.com", db=db,
        deal_type="sale", city="תל אביב - יפו", limit=50, view="all",
    )
    assert len(result) == 1
    assert result[0]["city"] == "תל אביב - יפו"
    assert result[0]["deal_type"] == "sale"


def test_empty_result_returns_empty_list():
    db = _make_db(all_props=[])
    result = list_properties(email="u@test.com", db=db, deal_type=None, city=None, limit=50, view="all")
    assert result == []
