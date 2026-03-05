"""Market trends: avg price and count by city, separated by sale vs rent."""
from fastapi import APIRouter, Depends

from api.deps import get_db, get_current_user_email
from database.db import DatabaseManager

router = APIRouter()


def _empty_trends():
    return {
        "total_ads": 0,
        "n_cities": 0,
        "cities": [],
        "by_city_sale": [],
        "by_city_rent": [],
        "total_sale": 0,
        "total_rent": 0,
        "avg_sale": 0,
        "avg_rent": 0,
    }


@router.get("/trends")
def get_trends(
    email: str = Depends(get_current_user_email),
    db: DatabaseManager = Depends(get_db),
    limit: int = 2000,
):
    """Returns trends with sale and rent separated (cities, by_city_sale, by_city_rent, totals, avgs)."""
    props = db.get_properties_for_analytics(user_email=email, limit=limit)
    if not props:
        return _empty_trends()
    # Normalize deal_type: "rent" vs "sale" (default)
    rows = []
    for p in props:
        price = p.get("price")
        if price is None:
            continue
        city = p.get("city") or "לא ידוע"
        deal_type = (p.get("deal_type") or "sale").strip().lower()
        if deal_type not in ("rent", "sale"):
            deal_type = "sale"
        rows.append({"city": city, "price": float(price), "deal_type": deal_type})
    if not rows:
        return _empty_trends()

    # Aggregate by city and deal_type
    sale_by_city: dict[str, list[float]] = {}
    rent_by_city: dict[str, list[float]] = {}
    for r in rows:
        c = r["city"]
        if r["deal_type"] == "rent":
            if c not in rent_by_city:
                rent_by_city[c] = []
            rent_by_city[c].append(r["price"])
        else:
            if c not in sale_by_city:
                sale_by_city[c] = []
            sale_by_city[c].append(r["price"])

    def build_by_city(by_city: dict[str, list[float]]):
        return [
            {"city": c, "avg_price": round(sum(prices) / len(prices)), "count": len(prices)}
            for c, prices in sorted(by_city.items(), key=lambda x: sum(x[1]) / len(x[1]))
        ]

    by_city_sale = build_by_city(sale_by_city)
    by_city_rent = build_by_city(rent_by_city)
    all_cities = sorted(set(sale_by_city.keys()) | set(rent_by_city.keys()))

    total_sale = sum(len(p) for p in sale_by_city.values())
    total_rent = sum(len(p) for p in rent_by_city.values())
    prices_sale = [r["price"] for r in rows if r["deal_type"] == "sale"]
    prices_rent = [r["price"] for r in rows if r["deal_type"] == "rent"]
    avg_sale = round(sum(prices_sale) / len(prices_sale)) if prices_sale else 0
    avg_rent = round(sum(prices_rent) / len(prices_rent)) if prices_rent else 0

    return {
        "total_ads": total_sale + total_rent,
        "n_cities": len(all_cities),
        "cities": all_cities,
        "by_city_sale": by_city_sale,
        "by_city_rent": by_city_rent,
        "total_sale": total_sale,
        "total_rent": total_rent,
        "avg_sale": avg_sale,
        "avg_rent": avg_rent,
    }
