import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection
from loguru import logger

from database.models import User, Property, UserSearch, WeeklyReport

# Load .env from repo root so MONGODB_* are set regardless of cwd
_db_dir = Path(__file__).resolve().parent
_repo_root = _db_dir.parent.parent
load_dotenv(_repo_root / ".env")
load_dotenv()  # current dir as fallback


def _make_mongo_client(uri: str) -> MongoClient:
    """Build MongoClient with TLS options that fix SSL handshake on Windows + Atlas."""
    opts = {"serverSelectionTimeoutMS": 25000}
    tls_insecure = os.getenv("MONGODB_TLS_INSECURE", "").strip().lower() in ("1", "true", "yes")

    if "mongodb+srv://" in uri:
        if tls_insecure:
            # Windows + Atlas: skip cert verification (dev only). Do NOT set tlsCAFile.
            opts["tlsAllowInvalidCertificates"] = True
        else:
            try:
                import certifi
                opts["tlsCAFile"] = certifi.where()
            except ImportError:
                pass
    return MongoClient(uri, **opts)


class DatabaseManager:
    def __init__(self, mongo_uri: Optional[str] = None):
        self.mongo_uri = mongo_uri or os.getenv(
            "MONGODB_URI",
            "mongodb://localhost:27017/aigent_realestate"
        )
        self.client = _make_mongo_client(self.mongo_uri)
        self.db = self.client.get_default_database("aigent_realestate")
        self._ensure_indexes()
        logger.info(f"MongoDB connected: {self.db.name}")

    def _ensure_indexes(self):
        self.db.users.create_index("email", unique=True)
        self.db.properties.create_index([("source", 1), ("source_id", 1)], unique=True, sparse=True)
        self.db.properties.create_index("matched_user_email")
        self.db.properties.create_index("found_at")
        self.db.properties.create_index("ai_score")
        self.db.login_tokens.create_index("token", unique=True)
        self.db.login_tokens.create_index([("expires_at", 1)], expireAfterSeconds=0)

    @property
    def users(self) -> Collection:
        return self.db.users

    @property
    def properties(self) -> Collection:
        return self.db.properties

    @property
    def searches(self) -> Collection:
        return self.db.searches

    @property
    def weekly_reports(self) -> Collection:
        return self.db.weekly_reports

    @property
    def login_tokens(self) -> Collection:
        return self.db.login_tokens

    # ─── Remember-me tokens (הישאר מחובר, תוקף 7 ימים) ─────────

    def create_remember_token(self, token: str, email: str, expires_at: datetime) -> None:
        self.login_tokens.delete_many({"email": email})
        self.login_tokens.insert_one({
            "token": token,
            "email": email,
            "expires_at": expires_at,
        })

    def get_email_by_remember_token(self, token: str) -> Optional[str]:
        # Reject non-string or suspiciously long tokens before touching the DB
        if not isinstance(token, str) or len(token) > 200:
            return None
        doc = self.login_tokens.find_one({"token": token})
        if not doc:
            return None
        expires_at = doc.get("expires_at")
        if expires_at:
            # MongoDB may return naive datetime; make comparable with UTC now
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) >= expires_at:
                self.login_tokens.delete_one({"token": token})
                return None
        return doc.get("email")

    # ─── Users ────────────────────────────────────────────────

    def upsert_user(self, user_data: dict) -> dict:
        user = User(**user_data)
        doc = user.model_dump()
        doc["updated_at"] = datetime.now(timezone.utc)
        created_at = doc.pop("created_at")
        result = self.users.find_one_and_update(
            {"email": user.email},
            {"$set": doc, "$setOnInsert": {"created_at": created_at}},
            upsert=True,
            return_document=True,
        )
        logger.info(f"User upserted: {result['email']}")
        return result

    def get_active_users(self) -> list[dict]:
        return list(self.users.find({"is_active": True}))

    def user_owns_email(self, requesting_email: str, target_email: str) -> bool:
        """Return True only when both emails are plain strings and are equal.
        Used to enforce that users can only access their own data.
        """
        if not isinstance(requesting_email, str) or not isinstance(target_email, str):
            return False
        return requesting_email.strip().lower() == target_email.strip().lower()

    def get_user_by_email(self, email: str) -> Optional[dict]:
        # Guard against NoSQL injection: only accept plain strings
        if not isinstance(email, str) or not email:
            return None
        return self.users.find_one({"email": email.strip().lower()})

    # ─── Properties ───────────────────────────────────────────

    def property_exists(self, source: str, source_id: str) -> bool:
        return self.properties.find_one(
            {"source": source, "source_id": source_id}
        ) is not None

    def get_property_by_source_id(self, source: str, source_id: str) -> Optional[dict]:
        return self.properties.find_one({"source": source, "source_id": source_id})

    def add_property(self, prop_data: dict) -> dict:
        now = datetime.now(timezone.utc)
        price = prop_data.get("price", 0)
        if "price_history" not in prop_data or not prop_data["price_history"]:
            prop_data = {**prop_data, "price_history": [{"price": price, "date": now}]}
        prop = Property(**prop_data)
        doc = prop.model_dump()
        if "date" in doc.get("price_history", [{}])[0]:
            doc["price_history"] = [
                {"price": e["price"], "date": e["date"] if hasattr(e["date"], "isoformat") else e["date"]}
                for e in doc["price_history"]
            ]
        result = self.properties.insert_one(doc)
        doc["_id"] = result.inserted_id
        logger.info(f"New property saved: {doc['city']} | {doc.get('rooms')}r | {doc['price']:,.0f}")
        return doc

    def update_property_on_price_drop(self, source: str, source_id: str, new_price: float,
                                      matched_user_email: Optional[str] = None, **extra) -> Optional[dict]:
        now = datetime.now(timezone.utc)
        result = self.properties.find_one_and_update(
            {"source": source, "source_id": source_id},
            {
                "$set": {
                    "price": new_price,
                    "price_drop": True,
                    "updated_at": now,
                    **{k: v for k, v in extra.items() if v is not None},
                },
                "$push": {
                    "price_history": {"price": new_price, "date": now},
                },
            },
            return_document=True,
        )
        if result:
            logger.info(f"Price drop updated: {source}/{source_id} -> {new_price:,.0f}₪")
        return result

    def get_unsent_properties(self, user_email: str) -> list[dict]:
        if not isinstance(user_email, str) or not user_email:
            return []
        return list(self.properties.find({
            "matched_user_email": user_email,
            "email_sent": False,
        }))

    def mark_email_sent(self, property_ids: list) -> None:
        from bson import ObjectId
        obj_ids = []
        for pid in property_ids:
            try:
                obj_ids.append(ObjectId(pid) if not isinstance(pid, ObjectId) else pid)
            except Exception:
                continue
        if obj_ids:
            self.properties.update_many(
                {"_id": {"$in": obj_ids}},
                {"$set": {"email_sent": True}},
            )

    def get_weekly_properties(self, user_email: str, days: int = 7) -> list[dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return list(self.properties.find(
            {"matched_user_email": user_email, "found_at": {"$gte": cutoff}},
        ).sort("ai_score", DESCENDING))

    def mark_report_sent(self, property_ids: list) -> None:
        from bson import ObjectId
        obj_ids = []
        for pid in property_ids:
            try:
                obj_ids.append(ObjectId(pid) if not isinstance(pid, ObjectId) else pid)
            except Exception:
                continue
        if obj_ids:
            self.properties.update_many(
                {"_id": {"$in": obj_ids}},
                {"$set": {"included_in_report": True}},
            )

    def get_all_properties_for_user(self, user_email: str, limit: int = 50) -> list[dict]:
        if not isinstance(user_email, str) or not user_email:
            return []
        return list(
            self.properties.find({"matched_user_email": user_email})
            .sort("found_at", DESCENDING)
            .limit(min(limit, 200))   # hard cap — callers cannot request unlimited docs
        )

    def get_latest_scan_properties(self, user_email: str, limit: int = 50) -> list[dict]:
        """Return properties from the most recent scan session (grouped by found_at proximity)."""
        if not isinstance(user_email, str) or not user_email:
            return []
        latest_search = self.searches.find_one(
            {"user_email": user_email},
            sort=[("executed_at", DESCENDING)],
        )
        if not latest_search:
            return []
        cutoff = latest_search["executed_at"] - timedelta(minutes=5)
        return list(
            self.properties.find({
                "matched_user_email": user_email,
                "found_at": {"$gte": cutoff},
            })
            .sort("found_at", DESCENDING)
            .limit(limit)
        )

    def get_avg_price_per_room_by_city(self, user_email: Optional[str] = None) -> dict[str, float]:
        """Average price per room by city (for Smart Value Estimator). Optional filter by user."""
        match = {"rooms": {"$gt": 0}, "price": {"$gt": 0}}
        if user_email:
            match["matched_user_email"] = user_email
        pipeline = [
            {"$match": match},
            {"$addFields": {"price_per_room": {"$divide": ["$price", "$rooms"]}}},
            {"$group": {"_id": "$city", "avg_price_per_room": {"$avg": "$price_per_room"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gte": 1}}},
        ]
        result = list(self.properties.aggregate(pipeline))
        return {doc["_id"]: doc["avg_price_per_room"] for doc in result}

    def get_properties_for_analytics(self, user_email: Optional[str] = None, limit: int = 5000) -> list[dict]:
        """Properties for market trends (time series). Optional filter by user."""
        query = {}
        if user_email:
            query["matched_user_email"] = user_email
        return list(
            self.properties.find(query, {"city": 1, "neighborhood": 1, "price": 1, "deal_type": 1, "found_at": 1, "price_history": 1})
            .sort("found_at", DESCENDING)
            .limit(limit)
        )

    # ─── Searches ─────────────────────────────────────────────

    def log_search(self, user_email: str, search_params: dict,
                   results_count: int, matches_count: int) -> None:
        search = UserSearch(
            user_email=user_email,
            search_params=search_params,
            results_count=results_count,
            matches_count=matches_count,
        )
        self.searches.insert_one(search.model_dump())

    # ─── Weekly Reports ───────────────────────────────────────

    def save_weekly_report(self, user_email: str, property_ids: list,
                           report_html: str) -> dict:
        report = WeeklyReport(
            user_email=user_email,
            property_ids=[str(pid) for pid in property_ids],
            total_properties=len(property_ids),
            report_html=report_html,
            sent_at=datetime.now(timezone.utc),
        )
        doc = report.model_dump()
        self.weekly_reports.insert_one(doc)
        return doc
