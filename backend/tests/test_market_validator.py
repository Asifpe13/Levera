import json

from services.market_validator import _extract_address_parts, _parse_grounded_response


def test_extract_address_parts_prefers_address_then_neighborhood_then_city():
  prop = {"city": "תל אביב - יפו", "address": "הרצל 10", "neighborhood": "לב העיר", "rooms": 3}
  street_or_area, city, rooms_str = _extract_address_parts(prop)
  assert street_or_area == "הרצל 10"
  assert city == "תל אביב - יפו"
  assert rooms_str == "3"

  prop2 = {"city": "חיפה", "neighborhood": "כרמל", "rooms": None}
  s2, c2, r2 = _extract_address_parts(prop2)
  assert s2 == "כרמל"
  assert c2 == "חיפה"
  assert r2 == "דומה"


def test_parse_grounded_response_accepts_plain_json():
  data = {"avg_price_per_sqm": 20000, "source_note": "נתוני מדינה", "confidence": 80}
  text = json.dumps(data)
  parsed = _parse_grounded_response(text)
  assert parsed == data


def test_parse_grounded_response_strips_markdown_code_block():
  inner = '{"avg_price_per_sqm": 18000, "source_note": "Gov", "confidence": 70}'
  wrapped = "```json\n" + inner + "\n```"
  parsed = _parse_grounded_response(wrapped)
  assert parsed is not None
  assert parsed["avg_price_per_sqm"] == 18000


def test_parse_grounded_response_fallback_number_range():
  # text with a single plausible price per sqm
  text = "ממוצע למ\"ר באזור זה הוא כ- 15500 ₪ לפי נתוני מדינה."
  parsed = _parse_grounded_response(text)
  assert parsed is not None
  assert 5000 < parsed["avg_price_per_sqm"] < 200000

